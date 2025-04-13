# Naive RAG System for Financial News

This project implements a basic Retrieval Augmented Generation (RAG) system for Vietnamese financial news articles. The system uses LangGraph to structure the RAG pipeline and provides a simple way to index and query financial news chunks.

## Features

- Simple, modular RAG pipeline using LangGraph
- Support for various chunk types (paragraphs, tables, images)
- Easy-to-use command line interface
- Configurable embedding model and LLM provider
- Type-safe implementation with Pydantic models

## Requirements

- Python 3.8+
- LangChain
- LangGraph
- Hugging Face Transformers
- Chroma DB
- Pydantic

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Create a `.env` file based on `.env.example`:
```bash
cp rag/.env.example .env
```
4. Update the `.env` file with your API keys:
```
OPENAI_API_KEY=your_openai_api_key
GOOGLE_API_KEY=your_google_api_key
HUGGINGFACE_TOKEN=your_huggingface_token
LLM_PROVIDER=google  # Use 'openai' or 'google'
```

## Usage

### Indexing Chunks

Before querying, you need to index your chunks. The system supports indexing either a single file or a directory containing multiple chunk files.

```bash
# Index a single file
python run_naive_rag.py index --file chunks/test.json_improved_chunks.json --collection finance_news

# Index all files in a directory
python run_naive_rag.py index --dir chunks --collection finance_news
```

### Querying

Once your chunks are indexed, you can query the system:

```bash
# Basic query
python run_naive_rag.py query --query "Nhà đầu tư tổ chức phi ngân hàng nắm bao nhiêu phần trăm trái phiếu doanh nghiệp?" --collection finance_news

# Verbose query (shows retrieved documents)
python run_naive_rag.py query --query "Ai là người phát biểu về thị trường trái phiếu?" --collection finance_news --verbose
```

## Architecture

The naive RAG system uses a simple three-node pipeline:

1. **Retrieval**: Fetches relevant documents from the vector store based on the query
2. **Context Formatting**: Formats the retrieved documents into a prompt-friendly context
3. **Generation**: Generates an answer based on the query and formatted context

The pipeline is implemented as a LangGraph, which provides a clean, declarative way to structure the RAG flow.

### State Schema

The system uses a Pydantic model to define the state:

```python
class RAGState(BaseModel):
    """State for the RAG pipeline."""
    query: str = Field(..., description="User query")
    retrieved_documents: List[Dict[str, Any]] = Field(
        default_factory=list, 
        description="Documents retrieved from the vector store"
    )
    formatted_context: str = Field(default="", description="Formatted context for the LLM")
    response: Optional[str] = Field(default=None, description="Final response to the user")
```

## File Structure

- `rag/naive_rag.py`: Core implementation of the naive RAG system
- `rag/config.py`: Configuration settings
- `run_naive_rag.py`: Command line interface for the system
- `chunks/`: Directory containing chunk files

## Extending the System

To extend the system:

1. **Custom Retrieval**: Modify the `retrieve_documents` function to implement custom retrieval logic
2. **Custom Formatting**: Update the `format_context` function to change how retrieved documents are formatted
3. **Different LLMs**: Update the `get_llm` function to use different LLM providers

## Limitations

This is a naive RAG implementation with some limitations:

- No query rewriting or reformulation
- Basic retrieval without reranking
- No memory of past interactions
- Limited to pre-indexed chunks 