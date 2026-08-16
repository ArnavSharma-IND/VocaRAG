import sys
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from backend.rag.embeddings import embedding_engine
from backend.rag.ingestion import ingestion_manager

@pytest.fixture(scope='session', autouse=True)
def setup_test_knowledge_base():
    embedding_engine.initialize()
    ingestion_manager.load_sample_knowledge_base()
