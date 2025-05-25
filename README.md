# Finance News Bot

AI-powered financial news analysis system using LangGraph agents and RAG pipeline for Vietnamese financial news.

## Features

- 🤖 **Multi-Agent System**: ReAct, Reflection, ReWOO, and Reflexion agents
- 📰 **News Processing**: Crawl and analyze Vietnamese financial news
- 🔍 **RAG Pipeline**: Advanced retrieval and generation capabilities
- 🗄️ **Vector Database**: ChromaDB integration for semantic search
- 🌐 **Multiple LLM Support**: OpenAI, Google, Anthropic, Fireworks

## Quick Start

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Setup environment**
   ```bash
   cp .env.example .env
   # Add your API keys to .env
   ```

3. **Run agents**
   ```bash
   # Start LangGraph server
   langgraph dev

   # Or run specific agent
   python -m src.agents.react_agent_graph
   ```

## Project Structure

```
src/
├── agents/          # LangGraph agent implementations
└── rag/            # RAG pipeline components
data/               # Raw and processed datasets
evaluation/         # Agent evaluation framework
examples/           # Usage examples
```

## Available Agents

- **ReAct Agent**: Reasoning and acting with tools
- **Reflection Agent**: Self-correcting responses
- **ReWOO Agent**: Reasoning without observation
- **Reflexion Agent**: Learning from feedback
- **Multi-Agent**: Collaborative agent system

## Requirements

- Python 3.11+
- API keys for chosen LLM provider
- See `requirements.txt` for dependencies

## License

MIT License - see [LICENSE](LICENSE) for details.
