import os
import argparse
from src.rag.embedding_utils import (
    create_chroma_client,
    create_collection,
    get_context_for_rag
)

def main():
    parser = argparse.ArgumentParser(description="Retrieve data using RAG for finance news")
    parser.add_argument(
        "--query", 
        type=str, 
        default="Thống kê thị trường trái phiếu doanh nghiệp riêng lẻ tháng 2/2025",
        help="Query to search for relevant information"
    )
    parser.add_argument(
        "--db_path", 
        type=str, 
        default="finance_news_vector_db",
        help="Path to the ChromaDB directory"
    )
    parser.add_argument(
        "--collection", 
        type=str, 
        default="finance_news",
        help="Name of the ChromaDB collection"
    )
    parser.add_argument(
        "--n_results", 
        type=int, 
        default=5,
        help="Number of results to retrieve"
    )
    
    args = parser.parse_args()
    
    client = create_chroma_client(args.db_path)
    
    collection = create_collection(client, args.collection)
    
    print(args.query)
    context = get_context_for_rag(
        query=args.query,
        collection=collection,
        n_results=args.n_results
    )
    
    print("\n=== Retrieved Context ===")
    print(context)
    print("\nYou can use this context to feed to an LLM for answering the query.")

if __name__ == "__main__":
    main() 