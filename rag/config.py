import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Data paths
DATA_PATHS = {
    "trai_phieu": "data/trai_phieu.json",
    "quoc_te": "data/quoc_te.json",
    "test": "data/test.json"
}

# Index paths
INDEX_STORE = "index_store"
CHROMA_DB_PATH = os.path.join(INDEX_STORE, "chroma_db")

# Model settings
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# API keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN")

# Retrieval settings
TOP_K = 5
CHUNK_SIZE = 256
CHUNK_OVERLAP = 64

# Use which LLM provider
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "google")  # 'openai' or 'google'