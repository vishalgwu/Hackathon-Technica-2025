import os
from dotenv import load_dotenv
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma



from openai import OpenAI
from .config import VECTOR_DIR
from .logger import get_logger

load_dotenv()
logger = get_logger(__name__)


# -----------------------------
# Load Vector DB
# -----------------------------
def get_vectordb():
    embed = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    vectordb = Chroma(
        embedding_function=embed,
        persist_directory=str(VECTOR_DIR),
    )
    return vectordb


# -----------------------------
# OPENAI Client (4o-mini)
# -----------------------------
def get_llm():
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return client


# -----------------------------
# RAG Answer Function
# -----------------------------
def answer_question(question, k=4):
    logger.info(f"Answering question: {question}")

    # retrieve docs
    vectordb = get_vectordb()
    retriever = vectordb.as_retriever(search_kwargs={"k": k})
    docs = retriever.invoke(question)

    if not docs:
        return {"answer": "No matching expenses found.", "sources": []}

    # build context
    context_parts = [
        f"Source {i} (file_id={doc.metadata.get('file_id')}):\n{doc.page_content}\n"
        for i, doc in enumerate(docs, start=1)
    ]
    context = "\n".join(context_parts)

    prompt = f"""
You are an expense analysis assistant.
Use ONLY the provided context.

Context:
{context}

Question:
{question}

Answer clearly and concisely.
"""

    llm = get_llm()
    response = llm.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    final_answer = response.choices[0].message.content

    sources = [
        {
            "file_id": doc.metadata.get("file_id"),
            "snippet": doc.page_content[:200]
        }
        for doc in docs
    ]

    return {"answer": final_answer, "sources": sources}


# CLI test
if __name__ == "__main__":
    q = input("Ask: ")
    out = answer_question(q)

    print("\n=== ANSWER ===")
    print(out["answer"])
    print("\n=== SOURCES ===")
    for s in out["sources"]:
        print(s)
