# Finance News Bot

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