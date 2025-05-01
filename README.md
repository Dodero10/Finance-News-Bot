# Finance News Bot

<<<<<<< HEAD
Finance News Bot is a modular system for crawling, processing, indexing, and querying Vietnamese financial news articles. It leverages advanced Retrieval Augmented Generation (RAG) techniques and modern LLMs to provide powerful search and summarization capabilities over financial news data.

## Features

- Automated crawling of financial news from sources like [TinNhanhChungKhoan](https://www.tinnhanhchungkhoan.vn)
- Modular RAG pipeline using LangGraph and LangChain
- Support for various chunk types (paragraphs, tables, images)
- Embedding and vector database support (ChromaDB, sentence-transformers)
- Configurable LLM provider (Google, OpenAI, Hugging Face)
- Type-safe implementation with Pydantic models
- Command-line and (optionally) web UI for interaction

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Setup Environment

- Copy the example environment file and update it with your API keys:
  ```bash
  cp rag/.env.example .env
  ```
- Edit `.env` with your credentials:
  ```
  OPENAI_API_KEY=your_openai_api_key
  GOOGLE_API_KEY=your_google_api_key
  HUGGINGFACE_TOKEN=your_huggingface_token
  LLM_PROVIDER=google  # or 'openai'
  ```

### 3. (Optional) Setup ChromeDriver for Crawling

- Download ChromeDriver matching your Chrome version
- Place it at: `E:\Thesis\Crawl\chromedriver-win64\chromedriver.exe`

### 4. Crawl Financial News

```bash
python crawl.py
```
Output will be saved to `tinnhanhchungkhoan_quoc_te.json`.

### 5. Preprocess and Chunk Data

```bash
python run_chunking.py
```

### 6. Index Chunks

```bash
python run_naive_rag.py index --file chunks/your_chunks.json --collection finance_news
```

### 7. Query the System

```bash
python run_naive_rag.py query --collection finance_news --query "Your question here"
```

## Directory Structure

- `crawl/` – Web crawlers for news sources
- `preprocessing/` – Data cleaning and chunking scripts
- `chunks/` – Processed and chunked data
- `rag/` – RAG pipeline and related utilities
- `frontend/` – (If present) Web UI for interaction
- `data/`, `index_store/` – Data and index storage
- `workflow/`, `scripts/`, `analysis/` – Additional utilities, analysis, and workflow automation

## Requirements

- Python 3.8+
- See [requirements.txt](requirements.txt) for full dependency list

## Documentation

- For more details, see the [Chainlit Documentation](https://docs.chainlit.io) if you are using the Chainlit UI.
- For RAG pipeline details, see the code and comments in the `rag/` directory.

## Notes

This project is under active development. Features, usage, and documentation may evolve.
=======
Finance News Bot is an end-to-end pipeline for crawling, processing, and enriching financial news articles, with a focus on Vietnamese sources such as [TinNhanhChungKhoan](https://www.tinnhanhchungkhoan.vn).

## Features

- **Automated Crawling**: Scrapes news articles (text, metadata, images) using Selenium and BeautifulSoup.
- **Image Content Extraction**: Uses Google Gemini (via Langchain) to parse image content and enrich articles with structured image metadata.
- **Data Preprocessing**: Utilities for cleaning, fixing, and transforming JSON datasets, including handling missing or problematic images.
- **Modular Design**: Clear separation of crawling, preprocessing, and workflow components for easy extension and maintenance.

## Project Structure

- `crawl/` — Contains the main crawler (`crawl.py`) for collecting articles.
- `preprocessing/` — Scripts for image extraction, fixing null images, and other data enrichment tasks. Includes its own README for details.
- `data/` — Stores raw and processed JSON datasets.
- `workflow/` — Advanced agentic and RAG pipelines (under development).
- `requirements.txt` — Python dependencies.
- `.env` — Store your Google Gemini API keys here.

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up ChromeDriver:**
   - Download ChromeDriver matching your Chrome version
   - Place it at: `E:\Thesis\Crawl\chromedriver-win64\chromedriver.exe`

3. **Add your Google Gemini API key:**
   - Create a `.env` file in the project root:
     ```
     GOOGLE_API_KEY=your_api_key_here
     ```

4. **Run the crawler:**
   ```bash
   python crawl/crawl.py
   ```
   Output will be saved to `data/tinnhanhchungkhoan_quoc_te.json`

5. **Process images in crawled data (optional):**
   See `preprocessing/README.md` for advanced image processing and metadata enrichment using Gemini.

## Notes

- This project is under active development. For advanced features and workflows, check the `workflow/` and `preprocessing/` directories.
- For details on image parsing and metadata, see `preprocessing/README.md`.
>>>>>>> feat/preprocessing
