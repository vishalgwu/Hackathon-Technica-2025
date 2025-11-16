from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from src.backend.store import load_vector_store, query_vector_store
from src.backend.ingestion_v2 import process_bank_statement

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)

@app.post("/process")
async def process_file(file: UploadFile = File(...)):
    parsed_expenses = process_bank_statement(file)
    return {"transactions": parsed_expenses}

@app.post("/query")
async def ask_question(payload: dict):
    question = payload["question"]

    # 1. Vector search
    search_results = query_vector_store(question)

    docs = "\n\n".join([r["content"] for r in search_results])

    prompt = f"""
You are a financial analysis AI.

User question:
{question}

Relevant transaction data:
{docs}

TASK:
- Answer based on the transactions only
- Provide a clean human-readable summary
- Include totals, top vendors, categories, insights
- No JSON unless user explicitly asks
"""

    from openai import OpenAI
    import os
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a financial analysis expert."},
            {"role": "user", "content": prompt}
        ]
    )

    answer = resp.choices[0].message.content.strip()

    return {"answer": answer, "matches": search_results}
