#!/usr/bin/env python
"""
Naive RAG implementation using LangGraph for financial news articles.
This implements a simple RAG pattern without advanced techniques.
"""

import os
import json
from typing import Dict, List, Any, Optional
from langchain_core.documents import Document
from langchain_core.runnables import RunnablePassthrough
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.schema.runnable import Runnable
from langchain.schema.runnable.config import RunnableConfig
from langchain_core.messages import HumanMessage, SystemMessage

from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field

from rag.config import (
    CHROMA_DB_PATH, EMBEDDING_MODEL, TOP_K, LLM_MODEL, GOOGLE_API_KEY, 
    OPENAI_API_KEY, LLM_PROVIDER, GEMINI_MODEL
)

# Define state with Pydantic for type safety
class RAGState(BaseModel):
    """State for the RAG pipeline."""
    query: str = Field(..., description="User query")
    retrieved_documents: List[Dict[str, Any]] = Field(
        default_factory=list, 
        description="Documents retrieved from the vector store"
    )
    formatted_context: str = Field(default="", description="Formatted context for the LLM")
    response: Optional[str] = Field(default=None, description="Final response to the user")

def get_embedding_model():
    """Initialize and return embedding model."""
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )

def get_llm():
    """Get the appropriate LLM based on config."""
    if LLM_PROVIDER == "openai":
        return ChatOpenAI(
            model=LLM_MODEL,
            openai_api_key=OPENAI_API_KEY,
        )
    elif LLM_PROVIDER == "google":
        return ChatOpenAI(
            model=GEMINI_MODEL,
            openai_api_key=GOOGLE_API_KEY,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {LLM_PROVIDER}")

def load_vector_store(collection_name: str = "default"):
    """Load the vector store from disk."""
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

def retrieve_documents(state: RAGState) -> RAGState:
    """Retrieve relevant documents for a query."""
    query = state.query
    
    try:
        # Get vector store
        vectorstore = load_vector_store()
        
        # Perform similarity search with scores
        results = vectorstore.similarity_search_with_score(
            query=query,
            k=TOP_K
        )
        
        # Format results
        documents = []
        for doc, score in results:
            documents.append({
                'content': doc.page_content,
                'metadata': doc.metadata,
                'score': score
            })
        
        # Update state with retrieved documents
        state.retrieved_documents = documents
        return state
    except Exception as e:
        print(f"Error retrieving documents: {e}")
        # Return original state if retrieval fails
        return state

def format_context(state: RAGState) -> RAGState:
    """Format retrieved documents into a prompt-friendly context."""
    documents = state.retrieved_documents
    context_parts = []
    
    for i, doc in enumerate(documents):
        metadata = doc['metadata']
        content = doc['content']
        chunk_type = metadata.get('chunk_type', 'unknown')
        
        # Format source information
        source_info = f"Title: {metadata.get('title', 'Unknown')}"
        if 'time_published' in metadata:
            source_info += f", Date: {metadata.get('time_published')}"
        
        # Handle different chunk types
        if chunk_type == 'paragraph':
            # Format paragraph with heading if available
            heading = metadata.get('heading', '')
            if heading and not content.startswith(heading):
                content = f"{heading}\n{content}"
                
            context_parts.append(
                f"Đoạn {i+1} (từ bài: {metadata.get('title', 'Unknown')}):\n{content}\n"
            )
            
        elif chunk_type == 'table':
            # Format table with caption
            caption = metadata.get('caption', 'Bảng dữ liệu')
            context_parts.append(
                f"Bảng {i+1} (từ bài: {metadata.get('title', 'Unknown')}):\n"
                f"Mô tả: {caption}\n{content}\n"
            )
            
        else:
            # Default format for other types
            context_parts.append(
                f"Tài liệu {i+1}:\n{content}\nNguồn: {source_info}\n"
            )
    
    state.formatted_context = "\n\n".join(context_parts)
    return state

def generate_answer(state: RAGState) -> RAGState:
    """Generate an answer based on the query and formatted context."""
    query = state.query
    context = state.formatted_context
    
    # Get LLM
    llm = get_llm()
    
    # Create prompt template
    prompt = ChatPromptTemplate.from_template(
        """Bạn là trợ lý AI chuyên về thông tin tài chính, trái phiếu và tin tức quốc tế.
        Dựa vào thông tin dưới đây, hãy trả lời câu hỏi của người dùng.
        
        THÔNG TIN:
        {context}
        
        CÂU HỎI: {query}
        
        Hãy trả lời một cách chính xác và đầy đủ dựa trên thông tin được cung cấp.
        Nếu thông tin không đủ để trả lời, hãy nói rằng bạn không có đủ thông tin.
        Trả lời bằng tiếng Việt, định dạng rõ ràng và dễ đọc.
        Nếu có thông tin từ bảng, hãy tham chiếu rõ ràng đến dữ liệu trong bảng.
        Nếu có thông tin từ nhiều nguồn, hãy tổng hợp thông tin từ tất cả các nguồn liên quan."""
    )
    
    # Generate response
    chain = prompt | llm | StrOutputParser()
    response = chain.invoke({
        "context": context,
        "query": query
    })
    
    state.response = response
    return state

def create_rag_graph() -> StateGraph:
    """Create a LangGraph for the RAG pipeline."""
    # Initialize the graph
    graph = StateGraph(RAGState)
    
    # Add nodes
    graph.add_node("retrieve", retrieve_documents)
    graph.add_node("format_context", format_context)
    graph.add_node("generate", generate_answer)
    
    # Add edges
    graph.add_edge("retrieve", "format_context")
    graph.add_edge("format_context", "generate")
    graph.add_edge("generate", END)
    
    # Set entry point
    graph.set_entry_point("retrieve")
    
    return graph

def naive_rag_query(query: str, collection_name: str = "default") -> Dict[str, Any]:
    """
    Execute a RAG query using the naive approach.
    
    Args:
        query: User query
        collection_name: Collection name for the vector store
        
    Returns:
        Dictionary with query, response, and retrieved documents
    """
    # Create the graph
    graph = create_rag_graph()
    
    # Compile the graph
    app = graph.compile()
    
    # Execute the graph with the input query
    result = app.invoke({"query": query})
    
    return {
        "query": query,
        "response": result.response,
        "documents": result.retrieved_documents
    }

def load_json_chunks(file_path: str) -> List[Dict[str, Any]]:
    """
    Load chunks from a JSON file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        List of chunks
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def create_vector_store_from_chunks(chunks: List[Dict[str, Any]], collection_name: str = "default"):
    """
    Create a vector store from chunks.
    
    Args:
        chunks: List of chunks
        collection_name: Collection name for the vector store
    """
    # Initialize embedding model
    embedding_model = get_embedding_model()
    
    # Convert chunks to documents
    documents = []
    for chunk in chunks:
        doc = Document(
            page_content=chunk['content'],
            metadata=chunk['metadata']
        )
        documents.append(doc)
    
    # Create vector store
    db = Chroma.from_documents(
        documents=documents,
        embedding=embedding_model,
        persist_directory=CHROMA_DB_PATH,
        collection_name=collection_name
    )
    
    # Persist to disk
    db.persist()
    
    return db

def index_chunks_file(file_path: str, collection_name: str = "default"):
    """
    Index chunks from a file.
    
    Args:
        file_path: Path to the chunks file
        collection_name: Collection name for the vector store
    """
    # Load chunks
    chunks = load_json_chunks(file_path)
    
    # Create vector store
    db = create_vector_store_from_chunks(chunks, collection_name)
    
    return {
        "file_path": file_path,
        "collection_name": collection_name,
        "num_chunks": len(chunks)
    }

if __name__ == "__main__":
    # Example usage
    import argparse
    
    parser = argparse.ArgumentParser(description="Naive RAG for financial news")
    parser.add_argument("--mode", choices=["index", "query"], required=True, 
                        help="Mode: index chunks or perform query")
    parser.add_argument("--file", help="Path to chunks file (for index mode)")
    parser.add_argument("--query", help="Query (for query mode)")
    parser.add_argument("--collection", default="default", help="Collection name")
    
    args = parser.parse_args()
    
    if args.mode == "index":
        if not args.file:
            parser.error("--file is required for index mode")
        result = index_chunks_file(args.file, args.collection)
        print(f"Indexed {result['num_chunks']} chunks from {result['file_path']} to collection {result['collection_name']}")
    
    elif args.mode == "query":
        if not args.query:
            parser.error("--query is required for query mode")
        result = naive_rag_query(args.query, args.collection)
        print(f"Query: {result['query']}")
        print(f"Response: {result['response']}")
        print(f"Retrieved {len(result['documents'])} documents") 