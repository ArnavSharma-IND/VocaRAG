import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SAMPLE_DOCS_DIR = DATA_DIR / "sample_docs"
UPLOAD_DIR = DATA_DIR / "uploads"
INDEX_STORAGE_DIR = DATA_DIR / "storage"

# Load environment variables
load_dotenv(BASE_DIR / ".env")

class Settings:
    PROJECT_NAME: str = "VocaRAG"
    VERSION: str = "1.0.0"
    TAGLINE: str = "Speak a question. Get a grounded answer."
    
    # Storage paths
    DATA_DIR: Path = DATA_DIR
    SAMPLE_DOCS_DIR: Path = SAMPLE_DOCS_DIR
    UPLOAD_DIR: Path = UPLOAD_DIR
    INDEX_STORAGE_DIR: Path = INDEX_STORAGE_DIR
    
    # LLM Configuration
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini").lower() # gemini | openai | demo
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    # Embedding Configuration
    EMBEDDING_MODEL_NAME: str = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
    EMBEDDING_DIMENSION: int = 384
    
    # Default RAG Parameters
    DEFAULT_CHUNK_STRATEGY: str = "recursive" # fixed | sentence | recursive
    DEFAULT_CHUNK_SIZE: int = 450
    DEFAULT_CHUNK_OVERLAP: int = 80
    DEFAULT_TOP_K: int = 4
    DEFAULT_SIMILARITY_THRESHOLD: float = 0.30
    
    # Guardrail thresholds
    # Calibrated against all-MiniLM-L6-v2:
    # Out-of-domain / fictional questions score <= 0.31
    # Valid in-corpus questions score >= 0.40
    CONFIDENCE_ABSTAIN_THRESHOLD: float = 0.35
    
    # Host & Ports
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

settings = Settings()

# Ensure directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_DOCS_DIR.mkdir(parents=True, exist_ok=True)
INDEX_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
