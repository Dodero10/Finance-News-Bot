from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from rag.config import (
    GOOGLE_API_KEY, OPENAI_API_KEY, CHROMA_DB_PATH, EMBEDDING_MODEL, TOP_K, LLM_PROVIDER
)
from langchain_huggingface import HuggingFaceEmbeddings
import os

def get_embedding_model():
    """Initialize and return embedding model."""

    
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )

def get_retriever(collection_name="default"):
    """Get retriever for a specific collection."""
    # Check if index exists
    if not os.path.exists(CHROMA_DB_PATH):
        raise FileNotFoundError(f"Vector store not found at {CHROMA_DB_PATH}")
    
    # Initialize embedding model
    embedding_model = get_embedding_model()
    
    # Load Chroma DB
    db = Chroma(
        persist_directory=CHROMA_DB_PATH,
        embedding_function=embedding_model,
        collection_name=collection_name
    )
    
    return db

def retrieve_documents(query, collection_name="default", top_k=None, filter_dict=None):
    """Retrieve relevant documents for a query with optional filtering."""
    if top_k is None:
        top_k = TOP_K
    
    # Get retriever
    db = get_retriever(collection_name)
    
    # Perform similarity search with scores and optional filtering
    results = db.similarity_search_with_score(
        query=query,
        k=top_k,
        filter=filter_dict
    )
    
    # Format results
    documents = []
    for doc, score in results:
        documents.append({
            'content': doc.page_content,
            'metadata': doc.metadata,
            'score': score
        })
    
    return documents

def retrieve_by_chunk_type(query, chunk_type, collection_name="default", top_k=None):
    """Retrieve documents of a specific chunk type."""
    filter_dict = {"chunk_type": chunk_type}
    return retrieve_documents(query, collection_name, top_k, filter_dict)

def retrieve_paragraphs(query, collection_name="default", top_k=None):
    """Retrieve paragraph chunks relevant to the query."""
    return retrieve_by_chunk_type(query, "paragraph", collection_name, top_k)

def retrieve_tables(query, collection_name="default", top_k=None):
    """Retrieve table chunks relevant to the query."""
    return retrieve_by_chunk_type(query, "table", collection_name, top_k)

def retrieve_full_article(article_id, collection_name="default"):
    """Retrieve the full article by its ID."""
    filter_dict = {
        "article_id": article_id,
        "chunk_type": "full_article"
    }
    result = retrieve_documents("", collection_name, 1, filter_dict)
    return result[0] if result else None

def retrieve_article_by_chunk(chunk_metadata, collection_name="default"):
    """Retrieve the full article associated with a retrieved chunk."""
    if "article_id" in chunk_metadata:
        return retrieve_full_article(chunk_metadata["article_id"], collection_name)
    return None

def retrieve_all_article_chunks(article_id, collection_name="default"):
    """Retrieve all chunks belonging to an article, sorted by paragraph order."""
    filter_dict = {"article_id": article_id}
    
    # Get retriever
    db = get_retriever(collection_name)
    
    # Use only filtering without semantic search
    docs = db.get(filter=filter_dict)
    
    # Format and sort results by paragraph_id if available
    results = []
    if docs and len(docs["documents"]) > 0:
        for i in range(len(docs["documents"])):
            # Create document object
            result = {
                "content": docs["documents"][i],
                "metadata": docs["metadatas"][i]
            }
            
            # Add to results
            results.append(result)
        
        # Sort by paragraph_id if it exists in metadata
        results = sorted(
            results, 
            key=lambda x: (
                x["metadata"].get("paragraph_id", 0), 
                x["metadata"].get("chunk_id", 0)
            ) if "paragraph_id" in x["metadata"] else 0
        )
    
    return results

def hybrid_search(query, collection_name="default", paragraph_weight=0.7, 
                 table_weight=0.3, top_k=None):
    """Perform hybrid search across paragraphs and tables with different weights."""
    if top_k is None:
        top_k = TOP_K
    
    # Retrieve paragraphs and tables
    paragraphs = retrieve_paragraphs(query, collection_name, top_k=top_k*2)
    tables = retrieve_tables(query, collection_name, top_k=top_k)
    
    # Adjust scores based on weights
    for p in paragraphs:
        p['score'] = p['score'] * paragraph_weight
    
    for t in tables:
        t['score'] = t['score'] * table_weight
    
    # Combine and sort by score
    combined = paragraphs + tables
    combined.sort(key=lambda x: x['score'])
    
    # Return top_k results
    return combined[:top_k]

def retrieve_with_context(query, collection_name="default", top_k=None):
    """Retrieve documents with surrounding context from the same article."""
    # First retrieve the most relevant documents
    results = retrieve_documents(query, collection_name, top_k)
    
    # Enhance with context
    enhanced_results = []
    seen_article_ids = set()
    
    for doc in results:
        article_id = doc['metadata'].get('article_id')
        
        # Skip if we've already processed this article
        if article_id in seen_article_ids:
            continue
            
        seen_article_ids.add(article_id)
        
        # Get the full article
        full_article = retrieve_full_article(article_id, collection_name)
        
        if full_article:
            # Add original result with its relevant score
            enhanced_results.append(doc)
            
            # Add the full article for context (at the end)
            enhanced_results.append(full_article)
    
    return enhanced_results
