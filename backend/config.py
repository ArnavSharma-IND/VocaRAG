import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data'
SAMPLE_DOCS_DIR = DATA_DIR / 'sample_docs'
UPLOAD_DIR = DATA_DIR / 'uploads'
INDEX_STORAGE_DIR = DATA_DIR / 'storage'
# Separate index directories for dual-collection architecture
ENTERPRISE_INDEX_DIR = INDEX_STORAGE_DIR / 'enterprise'
MSMARCO_INDEX_DIR = INDEX_STORAGE_DIR / 'msmarco'

# Load environment variables
load_dotenv(BASE_DIR / '.env')

class Settings:
    PROJECT_NAME: str = 'VocaRAG'
    VERSION: str = '2.0.0'
    TAGLINE: str = 'Speak a question. Get a grounded answer.'
    
    # Storage paths
    DATA_DIR: Path = DATA_DIR
    SAMPLE_DOCS_DIR: Path = SAMPLE_DOCS_DIR
    UPLOAD_DIR: Path = UPLOAD_DIR
    INDEX_STORAGE_DIR: Path = INDEX_STORAGE_DIR
    ENTERPRISE_INDEX_DIR: Path = ENTERPRISE_INDEX_DIR
    MSMARCO_INDEX_DIR: Path = MSMARCO_INDEX_DIR
    
    # LLM Configuration
    LLM_PROVIDER: str = os.getenv('LLM_PROVIDER', 'groq').lower()  # groq | gemini | openai | demo
    GEMINI_API_KEY: str = os.getenv('GEMINI_API_KEY', '')
    GEMINI_MODEL: str = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')
    
    OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY', '')
    OPENAI_BASE_URL: str = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
    OPENAI_MODEL: str = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    
    # Groq (LPU fast-path generation)
    GROQ_API_KEY: str = os.getenv('GROQ_API_KEY', '')
    GROQ_MODEL: str = os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')
    
    # Sarvam AI STT Configuration
    SARVAM_API_KEY: str = os.getenv('SARVAM_API_KEY', '')
    SARVAM_MODEL: str = os.getenv('SARVAM_MODEL', 'saaras:v3')
    SARVAM_DEFAULT_LANGUAGE: str = os.getenv('SARVAM_DEFAULT_LANGUAGE', 'hi-IN')
    SARVAM_API_URL: str = 'https://api.sarvam.ai/speech-to-text'
    
    # Embedding Configuration - multilingual model for Indic language support
    EMBEDDING_MODEL_NAME: str = os.getenv('EMBEDDING_MODEL_NAME', 'paraphrase-multilingual-mpnet-base-v2')
    EMBEDDING_DIMENSION: int = 768
    
    # MSMARCO-XI Dataset Configuration
    MSMARCO_ENABLED: bool = os.getenv('MSMARCO_ENABLED', 'true').lower() == 'true'
    MSMARCO_LANGUAGES: list = os.getenv('MSMARCO_LANGUAGES', 'hi,te,en').split(',')
    MSMARCO_SLICE_SIZES: dict = {
        'hi': int(os.getenv('MSMARCO_SLICE_SIZE_HI', '1000')),
        'te': int(os.getenv('MSMARCO_SLICE_SIZE_TE', '500')),
        'en': int(os.getenv('MSMARCO_SLICE_SIZE_EN', '300')),
    }
    MSMARCO_RAW_OVERSAMPLE: float = 1.5  # Pull 1.5x raw rows to account for junk passages
    
    # Default RAG Parameters
    DEFAULT_CHUNK_STRATEGY: str = 'recursive'  # fixed | sentence | recursive | semantic
    DEFAULT_CHUNK_SIZE: int = 450
    DEFAULT_CHUNK_OVERLAP: int = 80
    DEFAULT_TOP_K: int = 4
    DEFAULT_SIMILARITY_THRESHOLD: float = 0.30
    
    # Guardrail thresholds
    # Recalibrated for paraphrase-multilingual-mpnet-base-v2:
    # Multilingual models produce slightly lower absolute similarities than MiniLM
    CONFIDENCE_ABSTAIN_THRESHOLD: float = 0.30
    GROUNDEDNESS_THRESHOLD: float = 0.35  # Post-generation groundedness check
    
    # Active collection for queries (enterprise | msmarco)
    DEFAULT_COLLECTION: str = 'enterprise'
    
    # Host & Ports
    HOST: str = os.getenv('HOST', '0.0.0.0')
    PORT: int = int(os.getenv('PORT', '8000'))

settings = Settings()

# Ensure directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_DOCS_DIR.mkdir(parents=True, exist_ok=True)
INDEX_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
ENTERPRISE_INDEX_DIR.mkdir(parents=True, exist_ok=True)
MSMARCO_INDEX_DIR.mkdir(parents=True, exist_ok=True)
