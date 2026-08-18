import sys
import os
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Optional ZeroGPU initialization
try:
    import spaces
    @spaces.GPU(duration=10)
    def _zero_gpu_init():
        return True
    _zero_gpu_init()
except Exception:
    pass

# Initialize embedding engine
from backend.rag.embeddings import embedding_engine
embedding_engine.initialize()

# Import the FastAPI application
from backend.main import app
import gradio as gr

# Build clean Gradio interface for HF Spaces health probes
with gr.Blocks(title="VocaRAG Live Interface") as demo:
    gr.Markdown("# 🎙️ VocaRAG — Voice-Enabled Multilingual Indic RAG")
    gr.Markdown(
        "Welcome to VocaRAG! The full interactive React web application is running at the root URL. "
        "Visit **[VocaRAG Web App](/)** to use the full voice interface, benchmark lab, and security playground."
    )

# Mount Gradio onto FastAPI so HF Spaces Gradio healthchecks pass cleanly
app = gr.mount_gradio_app(app, demo, path="/gradio")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
