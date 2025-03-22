import json
import os
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from rag.config import GOOGLE_API_KEY, OPENAI_API_KEY, EMBEDDING_MODEL, LLM_PROVIDER
from rag.retriever import retrieve_documents
from rag.generator import generate_answer
from rag.retriever import (
    retrieve_documents, retrieve_paragraphs,
    retrieve_tables, hybrid_search
)
from chromadb import PersistentClient
from rag.generator import smart_generate_answer
from rag.retriever import retrieve_documents


def get_collection_stats(collection_name, chroma_path):
    """Get statistics about a collection."""
    try:

        # Initialize embedding model
        if LLM_PROVIDER == "google":
            embedding_model = OpenAIEmbeddings(
                model=EMBEDDING_MODEL,
                openai_api_key=GOOGLE_API_KEY,
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            )
        else:
            embedding_model = OpenAIEmbeddings(
                model=EMBEDDING_MODEL,
                openai_api_key=OPENAI_API_KEY
            )

        # Load collection
        db = Chroma(
            persist_directory=chroma_path,
            embedding_function=embedding_model,
            collection_name=collection_name
        )

        # Get collection stats
        count = db._collection.count()

        # Get document type counts if possible
        try:
            # Try to count by chunk type
            chunk_types = db._collection.get(
                where={"chunk_type": {"$exists": True}},
                include=["metadatas"]
            )

            # Count each chunk type
            type_counts = {}
            if chunk_types and "metadatas" in chunk_types:
                for metadata in chunk_types["metadatas"]:
                    chunk_type = metadata.get("chunk_type", "unknown")
                    type_counts[chunk_type] = type_counts.get(
                        chunk_type, 0) + 1
        except:
            type_counts = {"unknown": count}

        return {
            "collection": collection_name,
            "document_count": count,
            "document_types": type_counts
        }

    except Exception as e:
        return {
            "collection": collection_name,
            "error": str(e)
        }


def list_collections(chroma_path):
    """List all collections in the Chroma DB."""
    try:

        # Connect to Chroma
        client = PersistentClient(path=chroma_path)

        # Get collections
        collections = client.list_collections()

        return [c.name for c in collections]

    except Exception as e:
        return {
            "error": str(e)
        }


def simple_rag_query(query, collection_name="default"):
    """Simple function to perform RAG query for testing."""

    # Retrieve documents
    documents = retrieve_documents(query, collection_name)

    # Generate answer
    answer = generate_answer(query, documents)

    return {
        "query": query,
        "answer": answer,
        "documents": documents
    }


def advanced_rag_query(query, collection_name="default", top_k=None):
    """Advanced RAG query using intelligent document retrieval."""

    # Get query classification and use smart answer generation
    answer = smart_generate_answer(query, collection_name, top_k)

    # Get standard documents for comparison
    documents = retrieve_documents(query, collection_name, top_k)

    return {
        "query": query,
        "answer": answer,
        "retrieved_documents": documents
    }


def compare_retrieval_methods(query, collection_name="default", top_k=5):
    """Compare different retrieval methods for a query."""

    # Get results from different methods
    standard_results = retrieve_documents(query, collection_name, top_k)
    paragraph_results = retrieve_paragraphs(query, collection_name, top_k)
    table_results = retrieve_tables(query, collection_name, top_k)
    hybrid_results = hybrid_search(query, collection_name, top_k=top_k)

    return {
        "query": query,
        "standard_results": [doc["metadata"] for doc in standard_results],
        "paragraph_results": [doc["metadata"] for doc in paragraph_results],
        "table_results": [doc["metadata"] for doc in table_results],
        "hybrid_results": [doc["metadata"] for doc in hybrid_results]
    }
