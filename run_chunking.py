#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
from rag.indexing import prepare_documents, create_chunks, save_chunks

def test_chunking():
    """Test the improved chunking process with test.json."""
    print("Testing improved chunking process...")
    
    # Create output directory
    os.makedirs("chunks", exist_ok=True)
    
    # Load test data
    data_folder = "data"
    for file in os.listdir(data_folder):
        if file.endswith(".json"):
            data_path = os.path.join(data_folder, file)
            output_path = os.path.join("chunks", f"{file}_improved_chunks.json")

            print(f"Loading data from {data_path}...")
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"Loaded {len(data)} articles")
            
            # Prepare documents
            print("Preparing documents...")
            documents = prepare_documents(data)
            print(f"Prepared {len(documents)} documents")
            
            # Create chunks with improved method
            print("Creating chunks with improved method...")
            chunks = create_chunks(documents)
            print(f"Created {len(chunks)} chunks")
            
            # Log chunk types and lengths
            chunk_types = {}
            chunk_lengths = []
            sub_chunks = 0
            for chunk in chunks:
                chunk_type = chunk['metadata'].get('chunk_type', 'unknown')
                chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
                chunk_lengths.append(len(chunk['content']))
                if chunk['metadata'].get('is_sub_chunk', False):
                    sub_chunks += 1
            
            print(f"Chunk types distribution: {chunk_types}")
            print(f"Number of sub-chunks: {sub_chunks}")
            print(f"Average chunk length: {sum(chunk_lengths)/len(chunk_lengths):.2f} characters")
            print(f"Min chunk length: {min(chunk_lengths)} characters")
            print(f"Max chunk length: {max(chunk_lengths)} characters")
            
            # Save chunks
            print(f"Saving chunks to {output_path}")
            save_chunks(chunks, output_path)
            print(f"Chunks saved to {output_path}")
            
            # Analyze the first few chunks for inspection
            print("\nSample of first few chunks:")
            for i, chunk in enumerate(chunks[:3]):
                print(f"\nChunk {i+1}:")
                print(f"Content: {chunk['content'][:100]}...")
                print(f"Metadata: {chunk['metadata']}")
            
            print("\nImproved chunking test completed!")

if __name__ == "__main__":
    test_chunking() 