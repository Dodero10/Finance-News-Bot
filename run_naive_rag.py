#!/usr/bin/env python
"""
Command line interface for the naive RAG system.
This script provides a simple way to index chunks and query the RAG system.
"""

import os
import argparse
import logging
from pathlib import Path
from rag.naive_rag import index_chunks_file, naive_rag_query
from rag.config import CHROMA_DB_PATH

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("naive_rag_cli")

def main():
    parser = argparse.ArgumentParser(description="Naive RAG system for financial news")
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Index command
    index_parser = subparsers.add_parser("index", help="Index chunks files")
    index_parser.add_argument("--file", help="Path to chunks file to index")
    index_parser.add_argument("--dir", help="Directory containing chunks files to index")
    index_parser.add_argument("--collection", default="default", help="Collection name")
    
    # Query command
    query_parser = subparsers.add_parser("query", help="Query the RAG system")
    query_parser.add_argument("--query", required=True, help="Query to run")
    query_parser.add_argument("--collection", default="default", help="Collection name to query")
    query_parser.add_argument("--verbose", action="store_true", help="Show retrieved documents")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Handle commands
    if args.command == "index":
        # Check if at least one of --file or --dir is provided
        if not args.file and not args.dir:
            parser.error("At least one of --file or --dir must be provided")
        
        # Index single file
        if args.file:
            logger.info(f"Indexing file: {args.file}")
            result = index_chunks_file(args.file, args.collection)
            logger.info(f"Indexed {result['num_chunks']} chunks from {result['file_path']} to collection {result['collection_name']}")
        
        # Index directory
        if args.dir:
            dir_path = Path(args.dir)
            if not dir_path.exists():
                parser.error(f"Directory {args.dir} does not exist")
            
            logger.info(f"Indexing all JSON files in directory: {args.dir}")
            
            # Get list of JSON files in directory
            json_files = list(dir_path.glob("*.json"))
            
            if not json_files:
                logger.warning(f"No JSON files found in directory: {args.dir}")
                return
            
            # Index each file
            total_chunks = 0
            for file_path in json_files:
                try:
                    logger.info(f"Indexing file: {file_path}")
                    result = index_chunks_file(str(file_path), args.collection)
                    total_chunks += result['num_chunks']
                    logger.info(f"Indexed {result['num_chunks']} chunks from {file_path}")
                except Exception as e:
                    logger.error(f"Error indexing file {file_path}: {e}")
            
            logger.info(f"Indexed a total of {total_chunks} chunks to collection {args.collection}")
    
    elif args.command == "query":
        # Make sure the index exists
        if not os.path.exists(CHROMA_DB_PATH):
            logger.error(f"Vector store not found at {CHROMA_DB_PATH}. Please index chunks first.")
            return
        
        logger.info(f"Running query: {args.query}")
        result = naive_rag_query(args.query, args.collection)
        
        print("\n" + "="*80)
        print(f"QUERY: {result['query']}")
        print("="*80)
        print("\nRESPONSE:")
        print(result['response'])
        print("\n" + "="*80)
        
        if args.verbose:
            print("\nRETRIEVED DOCUMENTS:")
            for i, doc in enumerate(result['documents']):
                print(f"\nDocument {i+1}:")
                print(f"Source: {doc['metadata'].get('title', 'Unknown')}")
                print(f"Type: {doc['metadata'].get('chunk_type', 'unknown')}")
                print(f"Score: {doc['score']}")
                print(f"Content: {doc['content'][:200]}...")
            print("="*80)
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 