---
title: VocaRAG - Voice Multilingual Indic RAG
emoji: 🎙️
colorFrom: green
colorTo: emerald
sdk: gradio
sdk_version: 4.44.0
app_file: app.py
pinned: false
---

# VocaRAG — Voice-Enabled Multilingual Retrieval-Augmented Generation

[![CI](https://github.com/ArnavSharma-IND/VocaRAG/actions/workflows/ci.yml/badge.svg)](https://github.com/ArnavSharma-IND/VocaRAG/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB.svg?logo=react)](https://reactjs.org/)
[![FAISS](https://img.shields.io/badge/FAISS-Vector%20Store-blue.svg)](https://github.com/facebookresearch/faiss)
[![Sarvam AI](https://img.shields.io/badge/Sarvam%20AI-Saaras%20v3%20STT-orange.svg)](https://www.sarvam.ai)
[![Groq LPU](https://img.shields.io/badge/Groq-LPU%20Fast--Path-f55036.svg)](https://groq.com)

> **Speak a question in Hindi, Telugu, or English. Get an exact, cited, hallucination-free grounded answer.**

Developed for **Hackathon / HHGoa'26 — Task #2**.

---

## 1. Architectural Highlights & Compliance

1. **Server-Side Multilingual STT (Sarvam AI Saaras v3)**: 
   Raw browser audio streams directly to Sarvam AI's REST endpoint supporting 23 Indian languages (`hi-IN`, `te-IN`, `bn-IN`, `ta-IN`, `en-IN`, etc.) with mode switching (`transcribe`, `translate`, `codemix`).
2. **AI4Bharat MSMARCO-XI Corpus**:
   Native ingestion and retrieval over `ai4bharat/MSMARCO-XI` (14 Indic languages) preserving gold relevance tags (`is_selected`) for formal Information Retrieval evaluation (Recall@k, MRR).
3. **Dual Knowledge Collection Architecture**:
   - **Indic MSMARCO-XI (Graded)**: Multilingual passage search and Q&A across Hindi, Telugu, and English.
   - **Enterprise Policies (Demo)**: Comprehensive corporate handbook, travel, security, and hardware documentation.
4. **Multilingual Dense Embeddings**:
   `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` (768-dimensional dense vector space) ensuring cross-lingual semantic alignment.
5. **Four Chunking Strategies**:
   - **Recursive Hierarchical**: Paragraph $\to$ line $\to$ sentence $\to$ word boundary descent.
   - **Semantic Boundary**: Embedding-cosine inflection point splitting.
   - **Sentence Grouping**: Overlapping sentence windows.
   - **Fixed-Size**: Word-boundary snapped token windows.
6. **Sub-250ms Groq LPU Fast-Path + Multi-Tier Fallbacks**:
   Instant low-latency generation via Groq `llama-3.3-70b-versatile`, with seamless fallback to Gemini 1.5 Flash, OpenAI GPT-4o-mini, or deterministic zero-API local synthesis.
7. **Two-Sided Guardrails & Hallucination Prevention**:
   - Pre-retrieval Prompt Injection & Jailbreak regex/pattern shields (English & transliterated Indic).
   - Post-retrieval Evidence Confidence Thresholding ($<30\%$ similarity triggers explicit abstention).
   - Post-generation Groundedness token-overlap verification against cited chunks.
8. **Real Stage Latency Telemetry & P50/P70/P100 Benchmarking**:
   Clear split between **Retrieval Pipeline** ($<200\text{ms}$ SLA) and **End-to-End Generation**.

---

## 2. Project Architecture

```
├── backend/
│   ├── main.py                  # FastAPI application with dual-collection lifespan
│   ├── config.py                # App configuration, thresholds & model parameters
│   ├── requirements.txt         # Python dependencies (FastAPI, FAISS, PyTorch, Datasets, Pytest)
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py           # Pydantic schemas with telemetry & collection routing
│   ├── rag/
│   │   ├── stt.py               # Sarvam AI Saaras v3 STT client with exponential retry
│   │   ├── msmarco_loader.py    # AI4Bharat MSMARCO-XI dataset loader & IR eval tracker
│   │   ├── chunking.py          # Fixed, Sentence, Recursive, and Semantic chunkers
│   │   ├── embeddings.py        # 768-dim Multilingual MPNet SentenceTransformer + MD5 cache
│   │   ├── retriever.py         # Dual FAISS IndexFlatIP vector stores (Enterprise + MSMARCO)
│   │   ├── ingestion.py         # Multi-format parser (PDF, TXT, DOCX) & collection indexer
│   │   ├── generator.py         # Groq LPU, Gemini, OpenAI & local deterministic grounded synthesizers
│   │   ├── guardrails.py        # Injection detector, evidence abstention & post-gen groundedness
│   │   ├── pipeline.py          # Staged voice-to-answer RAG orchestrator with timestamping
│   │   └── benchmark.py         # 16-query evaluation suite & empirical percentile calculator
│   └── routes/
│       ├── ask.py               # POST /api/ask (voice/text -> grounded answer)
│       ├── stt.py               # POST /api/stt/transcribe (Sarvam audio upload)
│       ├── ingestion.py         # POST /api/ingest, POST /api/reindex, GET /api/documents
│       ├── retrieval.py         # POST /api/retrieval/search (Isolated FAISS sandbox)
│       ├── benchmark.py         # POST /api/benchmark/run, GET /api/benchmark/latest
│       ├── guardrails.py        # POST /api/guardrails/check, GET /api/guardrails/rules
│       └── system.py            # GET /api/system, GET /api/health
├── frontend/
│   ├── src/
│   │   ├── App.tsx              # Root container & navigation
│   │   ├── hooks/
│   │   │   └── useSpeechRecognition.ts  # MediaRecorder + Sarvam STT hook
│   │   ├── components/
│   │   │   ├── VoiceHero.tsx    # Mic, Sarvam language picker & collection switcher
│   │   │   ├── PipelineVisualizer.tsx # Animated stage execution graph
│   │   │   ├── AnswerCard.tsx   # Grounded response, confidence & citations
│   │   │   ├── SourceDrawer.tsx # Slide-out chunk context inspector
│   │   │   └── LatencyBreakdown.tsx # Telemetry metrics
│   │   └── pages/
│   │       ├── AskPage.tsx
│   │       ├── KnowledgeBasePage.tsx # Chunking studio & collection manager
│   │       ├── RetrievalLabPage.tsx  # Vector search playground
│   │       └── BenchmarkLabPage.tsx  # Dual percentile latency charts
├── tests/
│   ├── conftest.py              # Pytest fixture initializing vector store
│   ├── test_rag_pipeline.py     # Groundedness, abstention, injection & semantic tests
│   └── test_api_endpoints.py    # Async HTTP tests for all FastAPI routes
├── .github/workflows/
│   └── ci.yml                   # Automated Pytest + Vite build CI pipeline
├── Dockerfile                   # Multi-stage production container build
├── docker-compose.yml           # Docker orchestration definition
└── README.md
```

---

## 3. Quickstart & Installation

### Prerequisites
- **Python 3.10+** (Tested on Python 3.11 / 3.14)
- **Node.js 18+** & npm

### 1. Environment Setup

```bash
# Copy template and fill your API keys
cp .env.example .env
```

### 2. Backend Setup

```bash
# Create and activate Python virtual environment
python -m venv venv
.\venv\Scripts\activate      # Windows
# source venv/bin/activate   # macOS / Linux

# Install dependencies
pip install -r backend/requirements.txt

# Start backend server
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
*Backend runs on `http://localhost:8000` (FastAPI docs at `/docs`).*

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```
*Frontend runs on `http://localhost:5173`.*

---

## 4. Running Automated Tests & Verification

```bash
# Run backend Pytest suite with detailed output
pytest tests/ -v

# Run frontend build check
cd frontend && npm run build
```

---

## 5. API Reference Summary

- `POST /api/ask`: Core RAG query with collection selection and microsecond telemetry.
- `POST /api/stt/transcribe`: Audio upload to Sarvam AI Saaras v3 STT.
- `POST /api/ingest`: Multipart file upload (PDF/TXT/DOCX/MD) to specified collection.
- `POST /api/reindex`: Reindexes collection with requested chunking strategy (Recursive, Semantic, Sentence, Fixed).
- `POST /api/retrieval/search`: Vector search sandbox with Top-K & threshold controls.
- `POST /api/benchmark/run`: Executes 16-query evaluation suite computing P50/P70/P100 percentiles.
- `GET /api/system`: Health, models, and active vector store statistics.

---

## 6. License

Developed for **HHGoa'26 — Task #2**. MIT License.