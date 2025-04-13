"""
RAG (Retrieval Augmented Generation) package for Finance News Bot.
"""

# Import main functionality
from rag.naive_rag import (
    naive_rag_query,
    index_chunks_file,
    create_vector_store_from_chunks,
    load_json_chunks
)

# Import utilities
from rag.utils import (
    simple_rag_query,
    advanced_rag_query,
    compare_retrieval_methods
)

__all__ = [
    'naive_rag_query',
    'index_chunks_file',
    'create_vector_store_from_chunks',
    'load_json_chunks',
    'simple_rag_query',
    'advanced_rag_query',
    'compare_retrieval_methods'
]
