from pathlib import Path
import os

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parents[2]

# Data directories
DATA_DIR = BASE_DIR / "data"
RAW_PDF_DIR = DATA_DIR / "raw_pdfs"
TEXT_DIR = DATA_DIR / "extracted_text"
STRUCTURED_DIR = DATA_DIR / "structured"
VECTOR_DIR = DATA_DIR / "vectorstore"

# Make sure folders exist
for p in [RAW_PDF_DIR, TEXT_DIR, STRUCTURED_DIR, VECTOR_DIR]:
    p.mkdir(parents=True, exist_ok=True)

# LLM model config
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

CHUNK_SIZE = 800
CHUNK_OVERLAP = 150
