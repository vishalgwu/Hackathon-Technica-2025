import os
import base64
import io
import re
import json

from pathlib import Path
from dotenv import load_dotenv

import fitz
import pandas as pd
import pytesseract
from PIL import Image
from openai import OpenAI

from .config import RAW_PDF_DIR, STRUCTURED_DIR
from .logger import get_logger

load_dotenv()
logger = get_logger(__name__)

# Tesseract setup
pytesseract.pytesseract.tesseract_cmd = os.getenv("TESSERACT_PATH")

# OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# =====================================================================
#  STRONG JSON CLEANUP
# =====================================================================
def clean_llm_json(text: str) -> str:
    text = text.replace("```json", "").replace("```", "")
    text = text.replace("\\", "")
    text = text.replace("“", '"').replace("”", '"').replace("’", "'")
    text = re.sub(r"[^\x00-\x7F]+", " ", text)

    text = re.sub(r",\s*}", "}", text)
    text = re.sub(r",\s*]", "]", text)
    return text.strip()


def safe_json_load(text: str):
    cleaned = clean_llm_json(text)

    match = re.search(r"\{[\s\S]*\}", cleaned)
    if match:
        try:
            return json.loads(match.group(0))
        except:
            pass

    # fallback JSON structure
    return {
        "vendor_store": None,
        "date": None,
        "items": [],
        "tax": None,
        "total_amount": None,
        "currency": None,
        "payment_method": None
    }


# =====================================================================
# PDF → IMAGES
# =====================================================================
def pdf_to_images(pdf_path: Path):
    images = []
    doc = fitz.open(pdf_path)
    for i in range(len(doc)):
        pix = doc[i].get_pixmap(dpi=200)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        images.append(img)
    return images


def image_to_base64(image: Image.Image):
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


# =====================================================================
# OCR
# =====================================================================
def ocr_image_with_openai(image):
    b64 = image_to_base64(image)
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": "Extract ALL text only."},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}
            ]
        }]
    )
    return resp.choices[0].message.content.strip()


def ocr_extract_text(image):
    local = pytesseract.image_to_string(image)
    if len(local.strip()) < 50:
        logger.info("Weak local OCR → using OpenAI Vision")
        return ocr_image_with_openai(image)
    return local


# =====================================================================
#  SPECIAL PARSER: CHASE BANK STATEMENT
# =====================================================================
def parse_chase_bank_statement(raw_text: str):
    """
    Converts a Chase bank statement into multiple mini receipts.
    """
    transactions = []

    # Pattern for lines like:
    # 09/29 Card Purchase ... -5.50
    pattern = r"(\d{2}/\d{2})\s+(.*?)\s+(-?\d+\.\d{2})"
    matches = re.findall(pattern, raw_text)

    for date, description, amount in matches:
        amount = float(amount)

        # ignore positive credits
        if amount > 0:
            continue

        transactions.append({
            "vendor_store": "Chase Bank",
            "date": date,
            "items": [{
                "description": description,
                "price": abs(amount)
            }],
            "tax": None,
            "total_amount": abs(amount),
            "currency": "USD",
            "payment_method": "Card"
        })

    return transactions


# =====================================================================
# LLM RECEIPT PARSER (Used for real receipts only)
# =====================================================================
def parse_receipt_llm(raw_text: str, file_id: str):
    # BANK STATEMENT DETECTED
    if "Chase Total Checking" in raw_text or "TRANSACTION DETAIL" in raw_text:
        logger.info(f"{file_id}: Detected CHASE bank statement → using bank parser")
        return parse_chase_bank_statement(raw_text)

    # Normal receipts → use LLM
    prompt = f"""
Extract this receipt to JSON with fields:
vendor_store, date, items, tax, total_amount, currency, payment_method.

ONLY RETURN RAW JSON.

Text:
{raw_text}
"""
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )

    parsed = safe_json_load(resp.choices[0].message.content)
    return [parsed]   # wrap single receipt in list for consistency


# =====================================================================
# INGEST ALL RECEIPTS (NOW OUTPUTS MULTIPLE MINI-RECEIPTS)
# =====================================================================
def ingest_all_receipts():
    rows = []

    for pdf in RAW_PDF_DIR.glob("*.pdf"):
        base_id = pdf.stem
        logger.info(f"Processing {base_id}")

        # OCR all pages
        images = pdf_to_images(pdf)
        raw = ""
        for img in images:
            raw += "\n" + ocr_extract_text(img)

        # PARSE → RETURNS A LIST NOW
        parsed_list = parse_receipt_llm(raw, base_id)

        # Each mini receipt becomes its own row
        for idx, receipt_json in enumerate(parsed_list, start=1):
            rows.append({
                "file_id": f"{base_id}_{idx}",
                "raw_text": raw,
                "parsed": json.dumps(receipt_json, indent=2),
            })

    df = pd.DataFrame(rows)
    STRUCTURED_DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(STRUCTURED_DIR / "expenses.parquet", index=False)
    logger.info("Saved structured data.")

    return df
# =====================================================================
#  API-FRIENDLY WRAPPER FOR SINGLE UPLOAD (Streamlit/FastAPI)
# =====================================================================
def process_bank_statement(uploaded_file):
    """
    Takes an uploaded PDF/image from FastAPI, saves it, runs OCR + parsing,
    and returns parsed receipts for THIS file only.
    """

    # 1. Save the uploaded file into RAW_PDF_DIR
    RAW_PDF_DIR.mkdir(parents=True, exist_ok=True)
    saved_path = RAW_PDF_DIR / uploaded_file.filename

    with open(saved_path, "wb") as f:
        f.write(uploaded_file.file.read())

    logger.info(f"Saved uploaded file: {saved_path}")

    # 2. Run ingestion on ALL PDFs (your pipeline processes all PDFs)
    df = ingest_all_receipts()

    # 3. Filter only rows belonging to this file
    base_id = saved_path.stem  # filename without .pdf
    filtered = df[df["file_id"].str.contains(base_id)]

    # 4. Convert the `parsed` JSON strings back into Python objects
    output = []
    for _, row in filtered.iterrows():
        output.append(json.loads(row["parsed"]))

    return output


if __name__ == "__main__":
    ingest_all_receipts()
