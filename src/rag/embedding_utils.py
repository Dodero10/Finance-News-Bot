import os
import json
from typing import List, Dict, Any, Optional
from tqdm import tqdm
import chromadb
from chromadb.utils import embedding_functions
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_embedding_model():
    """
    Returns the cheapest OpenAI embedding model.
    Currently, this is 'text-embedding-3-small'.
    """
    return "text-embedding-3-small"

def get_openai_ef():
    """
    Returns an OpenAI embedding function for ChromaDB.
    """
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=os.getenv("OPENAI_API_KEY"),
        model_name=get_embedding_model()
    )
    return openai_ef

def create_chroma_client(persist_directory: str = "finance_news_vector_db"):
    """
    Creates and returns a ChromaDB client with the specified persist directory.
    
    Args:
        persist_directory: Directory where ChromaDB will store data
        
    Returns:
        A ChromaDB client
    """
    return chromadb.PersistentClient(path=persist_directory)

def create_collection(client, collection_name: str = "finance_news"):
    """
    Creates a new collection in ChromaDB or gets an existing one.
    
    Args:
        client: ChromaDB client
        collection_name: Name of the collection
        
    Returns:
        A ChromaDB collection
    """
    openai_ef = get_openai_ef()
    
    try:
        # Try to get existing collection
        collection = client.get_collection(
            name=collection_name,
            embedding_function=openai_ef
        )
        print(f"Using existing collection: {collection_name}")
    except:
        # Create new collection if it doesn't exist
        collection = client.create_collection(
            name=collection_name,
            embedding_function=openai_ef
        )
        print(f"Created new collection: {collection_name}")
    
    return collection

def sanitize_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize metadata by removing or flattening complex structures.
    ChromaDB only supports primitive types (str, int, float, bool) for metadata values.
    
    Args:
        metadata: Original metadata dictionary
        
    Returns:
        Sanitized metadata dictionary with only primitive types
    """
    sanitized = {}
    
    for key, value in metadata.items():
        # Skip 'images' field entirely as it's a list of complex objects
        if key == 'images':
            continue
            
        # Handle simple types (directly supported by ChromaDB)
        if isinstance(value, (str, int, float, bool)) or value is None:
            sanitized[key] = value
        # For lists, join elements if they're strings, otherwise skip
        elif isinstance(value, list):
            # Skip lists that aren't simple strings
            if all(isinstance(item, str) for item in value):
                sanitized[key] = ", ".join(value)
        # For dictionaries, skip entirely for simplicity
        elif isinstance(value, dict):
            # Skip nested dicts
            continue
    
    # Ensure we have at least a basic set of metadata fields
    if "article_id" not in sanitized and "article_id" in metadata:
        sanitized["article_id"] = metadata["article_id"]
        
    if "title" not in sanitized and "title" in metadata:
        sanitized["title"] = metadata["title"]
    
    return sanitized

def embed_and_store_chunks(
    file_path: str,
    collection,
    batch_size: int = 100
):
    """
    Embeds chunks from a JSON file and stores them in a ChromaDB collection.
    
    Args:
        file_path: Path to the JSON file containing chunks
        collection: ChromaDB collection
        batch_size: Number of chunks to process at once
    """
    # Load chunks from JSON file
    with open(file_path, 'r', encoding='utf-8') as f:
        chunks = json.load(f)
    
    # Process chunks in batches
    for i in tqdm(range(0, len(chunks), batch_size)):
        batch = chunks[i:i+batch_size]
        
        # Prepare data for ChromaDB
        ids = [f"chunk_{i+j}" for j in range(len(batch))]
        documents = [chunk["content"] for chunk in batch]
        
        # Sanitize metadata to ensure compatibility with ChromaDB
        metadatas = [sanitize_metadata(chunk["metadata"]) for chunk in batch]
        
        # Add documents to collection
        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
    
    print(f"Successfully embedded and stored {len(chunks)} chunks")

def retrieve_similar_chunks(
    collection,
    query: str,
    n_results: int = 5,
    filter_criteria: Optional[Dict[str, Any]] = None
):
    """
    Retrieves chunks similar to the query from the collection.
    
    Args:
        collection: ChromaDB collection
        query: Query string
        n_results: Number of similar chunks to retrieve
        filter_criteria: Optional filter to apply to the query
        
    Returns:
        List of retrieved documents and their metadata
    """
    # Query the collection
    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        where=filter_criteria
    )
    
    # Format results
    retrieved_results = []
    for i in range(len(results["documents"][0])):
        retrieved_results.append({
            "content": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i]
        })
    
    return retrieved_results

def get_context_for_rag(
    query: str,
    collection,
    n_results: int = 5,
    filter_criteria: Optional[Dict[str, Any]] = None
):
    """
    Retrieves context for RAG based on a query.
    
    Args:
        query: User query
        collection: ChromaDB collection
        n_results: Number of chunks to retrieve
        filter_criteria: Optional filter to apply to the query
        
    Returns:
        Formatted context string for RAG
    """
    # Retrieve similar chunks
    retrieved_chunks = retrieve_similar_chunks(
        collection=collection,
        query=query,
        n_results=n_results,
        filter_criteria=filter_criteria
    )
    
    # Format context
    context = ""
    for i, chunk in enumerate(retrieved_chunks):
        context += f"\n--- Document {i+1} ---\n"
        context += f"Content: {chunk['content']}\n"
        
        # Add metadata
        context += "Metadata:\n"
        for key, value in chunk["metadata"].items():
            context += f"  - {key}: {value}\n"
    
    return context 

def retrieve_from_db(
    query: str,
    db_path: str = "finance_news_vector_db",
    collection_name: str = "finance_news",
    n_results: int = 5,
    filter_criteria: Optional[Dict[str, Any]] = None,
    return_formatted: bool = True
):
    """
    Simple function to retrieve data from ChromaDB from outside the module.
    
    Args:
        query: The query string to search for
        db_path: Path to the ChromaDB database
        collection_name: Name of the collection to query
        n_results: Number of results to return
        filter_criteria: Optional filter criteria for the query
        return_formatted: If True, returns formatted context for RAG, otherwise returns raw chunks
        
    Returns:
        Either formatted context string or list of retrieved chunks
    """
    # Create ChromaDB client
    client = create_chroma_client(db_path)
    
    # Get collection
    collection = create_collection(client, collection_name)
    
    if return_formatted:
        # Return formatted context for RAG
        return get_context_for_rag(
            query=query,
            collection=collection,
            n_results=n_results,
            filter_criteria=filter_criteria
        )
    else:
        # Return raw chunks
        return retrieve_similar_chunks(
            collection=collection,
            query=query,
            n_results=n_results,
            filter_criteria=filter_criteria
        ) 