import argparse
import os
from rag.indexing import index_dataset
from rag.config import DATA_PATHS, INDEX_STORE

def main():
    parser = argparse.ArgumentParser(description='Index data for RAG system')
    parser.add_argument('--dataset', '-d', choices=['trai_phieu', 'quoc_te', 'all'], 
                      default='all', help='Dataset to index')
    parser.add_argument('--save-docs', action='store_true', 
                      help='Save prepared documents to JSON')
    parser.add_argument('--output-dir', '-o', default='prepared_docs',
                      help='Directory to save prepared documents')
    
    args = parser.parse_args()
    
    # Create index directory if it doesn't exist
    os.makedirs(INDEX_STORE, exist_ok=True)
    
    # Create output directory if saving docs
    if args.save_docs:
        os.makedirs(args.output_dir, exist_ok=True)
    
    if args.dataset == 'all':
        # Index all datasets
        for name, path in DATA_PATHS.items():
            print(f"=== Indexing dataset: {name} ===")
            
            # Determine output path if saving docs
            docs_output_path = None
            if args.save_docs:
                docs_output_path = os.path.join(args.output_dir, f"{name}_prepared.json")
            
            # Index with or without saving prepared documents
            index_dataset(
                data_path=path, 
                index_name=name,
                save_docs=args.save_docs,
                docs_output_path=docs_output_path
            )
            
            print(f"=== Completed indexing: {name} ===\n")
    else:
        # Index specific dataset
        path = DATA_PATHS.get(args.dataset)
        if not path:
            print(f"Dataset {args.dataset} not found in config.")
            return
        
        # Determine output path if saving docs
        docs_output_path = None
        if args.save_docs:
            docs_output_path = os.path.join(args.output_dir, f"{args.dataset}_prepared.json")
        
        print(f"=== Indexing dataset: {args.dataset} ===")
        
        # Index with or without saving prepared documents
        index_dataset(
            data_path=path, 
            index_name=args.dataset,
            save_docs=args.save_docs,
            docs_output_path=docs_output_path
        )
        
        print(f"=== Completed indexing: {args.dataset} ===")

if __name__ == "__main__":
    main()
