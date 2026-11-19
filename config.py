"""Shared configuration for the local-first academy assistant."""
from pathlib import Path
import os
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1").rstrip("/")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-oss-20b")
QDRANT_PATH = Path(os.getenv("QDRANT_PATH", str(ROOT / "qdrant_db")))
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "full_stack_academy_docs")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
TTS_ENGINE = os.getenv("TTS_ENGINE", "pyttsx3").lower()
TTS_VOICE = os.getenv("TTS_VOICE", "default")
PIPER_EXECUTABLE = os.getenv("PIPER_EXECUTABLE", "piper")
DOCS_DIR = ROOT / "docs"
