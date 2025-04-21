# Financial News RAG with LangGraph Tool Agent

This module implements a naive Retrieval-Augmented Generation (RAG) system for financial news data using LangGraph. The system provides a tool agent that can answer questions about financial news using the RAG pipeline.

## Architecture

The system consists of two main components:

1. **Finance News RAG**: A RAG pipeline that uses financial news data to answer questions.
2. **Finance Tool Agent**: A tool-based agent that uses the RAG system to answer user questions.

### RAG Pipeline Architecture

The RAG pipeline follows these steps:

1. **Query Generation**: Generates search queries from the user's question to maximize retrieval effectiveness.
2. **Document Retrieval**: Retrieves relevant documents from a vector store using the generated queries.
3. **Answer Generation**: Generates a comprehensive answer based on the retrieved documents.

The graph structure is implemented using LangGraph's declarative API, ensuring clear state transitions and node relationships.

```
generate_search_queries → retrieve_documents → generate_answer
```

### Tool Agent Architecture

The tool agent is built around a two-node graph:

1. **Agent Node**: Processes user messages and decides whether to use tools or respond directly.
2. **Action Node**: Executes tool calls based on the agent's decisions.

The agent uses a dynamic decision-making process to determine the flow:

```
     ┌─────────┐
     │         │
     ▼         │
 ┌───────┐  ┌────────┐
 │ agent │→→│ action │
 └───────┘  └────────┘
     │
     ▼
    END
```

## Components

### State Schemas

#### RAG State
```python
class RAGState(TypedDict):
    question: str
    context: List[Dict[str, Any]]
    generation: Optional[str]
    search_queries: Optional[List[str]]
    documents: Optional[List[Dict[str, Any]]]
    answer: Optional[str]
```

#### Agent State
```python
class AgentState(TypedDict):
    messages: List[Union[HumanMessage, AIMessage, ToolMessage, SystemMessage]]
    next: Optional[str]
```

### Key Modules

- `finance_rag.py`: Implements the RAG system using LangGraph.
- `tool_agent.py`: Implements the Tool Agent using LangGraph with the RAG system.
- `example.py`: Provides example usage of the RAG and Tool Agent system.

## Usage

```python
# Initialize RAG system and load data
rag = FinanceNewsRAG()
rag.load_data()

# Initialize tool agent
agent = FinanceToolAgent()

# Process a question
messages = agent.invoke("What are the latest trends in bond markets?")

# Print the conversation
for msg in messages:
    print(f"{msg.type}: {msg.content}")
```

## Tools Available

The tool agent provides the following tools:

- `search_financial_news`: Search for financial news information using the RAG system.
- `get_market_summary`: Get a summary of a specified financial market.
- `get_company_info`: Get information about a specific company by stock symbol.

## Implementation Notes

1. **Modular Design**: Each component is designed to be modular and extensible, with clear interfaces.
2. **State Management**: All state transitions are explicit, with well-defined state schemas.
3. **Error Handling**: Basic error handling is included, with clear error messages.
4. **Vector Store**: Uses FAISS for efficient vector similarity search.
5. **LLM Integration**: Uses Google Gemini for powerful language model capabilities.

## Requirements

- Google Gemini API key (set in `.env` file)
- FAISS for vector storage
- LangGraph for workflow orchestration
- LangChain for LLM and embedding integration

## Future Enhancements

1. Add streaming support for real-time responses
2. Implement more sophisticated query generation techniques
3. Add structured output parsing for tool calls
4. Implement caching for improved performance
5. Add monitoring and observability features 