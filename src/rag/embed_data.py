import os
import argparse
from src.rag.embedding_utils import (
    create_chroma_client,
    create_collection,
    embed_and_store_chunks
)

def main():
    parser = argparse.ArgumentParser(description="Embed finance news data into ChromaDB")
    parser.add_argument(
        "--input", 
        type=str, 
        default="data/chunks/quoc_te.json_improved_chunks.json",
        help="Path to the input chunks JSON file"
    )
    parser.add_argument(
        "--db_path", 
        type=str, 
        default="finance_news_vector_db",
        help="Path to store the ChromaDB files"
    )
    parser.add_argument(
        "--collection", 
        type=str, 
        default="finance_news",
        help="Name of the ChromaDB collection"
    )
    parser.add_argument(
        "--batch_size", 
        type=int, 
        default=100,
        help="Batch size for processing chunks"
    )
    
    args = parser.parse_args()
    
    # Create ChromaDB client
    client = create_chroma_client(args.db_path)
    
    # Create or get collection
    collection = create_collection(client, args.collection)
    
    # Embed and store chunks
    embed_and_store_chunks(
        file_path=args.input,
        collection=collection,
        batch_size=args.batch_size
    )
    
    print("Embedding complete!")

if __name__ == "__main__":
    main() 