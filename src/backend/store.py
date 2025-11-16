import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document

from .config import STRUCTURED_DIR, VECTOR_DIR
from .logger import get_logger

logger = get_logger(__name__)


############################################################
# BUILD VECTOR STORE (CALLED AFTER INGESTION)
############################################################
def build_vectorstore():
    logger.info("Loading structured data...")

    df_path = STRUCTURED_DIR / "expenses.parquet"
    if not df_path.exists():
        logger.error("No expenses.parquet file found. Run ingestion first.")
        return None

    df = pd.read_parquet(df_path)

    logger.info("Converting rows into documents...")
    docs = []
    for _, row in df.iterrows():
        parsed_preview = str(row["parsed"])[:500]

        text = (
            f"File ID: {row['file_id']}.\n"
            f"Raw text: {row['raw_text'][:500]}\n"
            f"Parsed JSON: {parsed_preview}"
        )

        docs.append(Document(
            page_content=text,
            metadata={"file_id": row["file_id"]}
        ))

    logger.info(f"Created {len(docs)} documents.")

    VECTOR_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("Building vectorstore using LOCAL embeddings...")

    embed_model = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    vectordb = Chroma.from_documents(
        documents=docs,
        embedding=embed_model,
        persist_directory=str(VECTOR_DIR)
    )

    vectordb.persist()
    logger.info(f"Vectorstore saved to: {VECTOR_DIR}")

    return vectordb



############################################################
# LOAD VECTOR STORE FOR QUERY (USED BY API + STREAMLIT)
############################################################

vectordb_cached = None  # Global cache for performance


def load_vector_store():
    """
    Loads an existing Chroma vectorstore from disk.
    Called once when backend starts.
    """
    global vectordb_cached

    embed_model = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    vectordb_cached = Chroma(
        embedding_function=embed_model,
        persist_directory=str(VECTOR_DIR)
    )

    logger.info("Vectorstore loaded successfully.")
    return vectordb_cached



############################################################
# SEMANTIC SEARCH FUNCTION
############################################################
def query_vector_store(query: str):
    """
    Performs semantic search on the vectorstore and returns top matches.
    """
    global vectordb_cached

    if vectordb_cached is None:
        load_vector_store()  # Auto-load if not loaded yet

    results = vectordb_cached.similarity_search_with_relevance_scores(query, k=5)

    output = []
    for doc, score in results:
        output.append({
            "score": float(score),
            "content": doc.page_content,
            "metadata": doc.metadata
        })

    return output



############################################################
# SCRIPT ENTRY POINT
############################################################
if __name__ == "__main__":
    build_vectorstore()
