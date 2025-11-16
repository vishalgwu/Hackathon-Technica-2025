from typing import Any, Dict, List
import json
import re

from .base import Agent
from src.backend.logger import get_logger
from openai import OpenAI

logger = get_logger(__name__)
from dotenv import load_dotenv
import os
from openai import OpenAI

load_dotenv()    # <--- IMPORTANT
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
from dotenv import load_dotenv
import os
from openai import OpenAI

load_dotenv()    # <--- IMPORTANT
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))



# ============================================================
# SAFE JSON LOAD (kept from your v2 logic)
# ============================================================
def safe_load_json(text: str) -> Dict:
    """
    Safely loads JSON from ingestion_v2 output.
    Never crashes. Always returns a dict.
    """

    if not text:
        return {}

    # Try direct load
    try:
        return json.loads(text)
    except:
        pass

    cleaned = text

    # Clean smart quotes
    cleaned = cleaned.replace("“", '"').replace("”", '"')

    # Remove illegal backslashes
    cleaned = re.sub(r'\\(?!["\\/bfnrt])', "", cleaned)

    # Remove invisible unicode
    cleaned = re.sub(r"[^\x00-\x7F]+", " ", cleaned)

    # Try again
    try:
        return json.loads(cleaned)
    except:
        pass

    # Extract JSON substring
    match = re.search(r"\{[\s\S]*\}", cleaned)
    if match:
        try:
            return json.loads(match.group())
        except:
            pass

    # Fallback — valid empty schema
    return {
        "vendor_store": None,
        "date": None,
        "items": [],
        "tax": None,
        "total_amount": None,
        "currency": None,
        "payment_method": None
    }


# ============================================================
# CATEGORY CLASSIFIER (LLM)
# ============================================================
def classify_category_llm(merchant: str, items: List[Dict], raw_text: str) -> str:
    """
    Uses GPT-4o-mini to classify the transaction.
    Always returns ONE category string.
    """

    # Build description context from items
    description_text = "; ".join(
        f"{i.get('description', '')}" for i in items
    )

    prompt = f"""
You are an expert financial classifier. 
Pick the BEST category for this transaction.

Choose EXACTLY ONE category from this list:
- Travel
- Transportation
- Meals
- Groceries
- Lodging
- Subscription
- Equipment
- Utilities
- Bank Statement
- Other

Merchant: {merchant}
Items: {description_text}
Full Receipt Text: {raw_text}

Return ONLY the category name. No explanation.
"""

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10
        )
        category = resp.choices[0].message.content.strip()

        logger.info(f"LLM classified → {category}")
        return category

    except Exception as e:
        logger.error(f"LLM category error: {e}")
        return None


# ============================================================
# STATIC CATEGORY FALLBACK (keywords)
# ============================================================
def static_category_classifier(text_lower: str) -> str:
    if any(x in text_lower for x in ["uber", "lyft", "taxi"]):
        return "Travel"
    if "mcdonald" in text_lower or "restaurant" in text_lower or "cafe" in text_lower:
        return "Meals"
    if "hotel" in text_lower:
        return "Lodging"
    if "bestbuy" in text_lower or "electronics" in text_lower:
        return "Equipment"
    if "costco" in text_lower or "wholefoods" in text_lower or "grocery" in text_lower:
        return "Groceries"
    if "linkedin" in text_lower or "openai" in text_lower:
        return "Subscription"
    if "utility" in text_lower:
        return "Utilities"

    return "Other"


# ============================================================
# EXTRACTION AGENT v3 — LLM + HYBRID
# ============================================================
class ExtractionAgent(Agent):
    """
    Extracts merchant, date, total, items, and AI category.
    """

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(">>> EXTRACTION AGENT V3 STARTED <<<")

        extracted = []
        raw_receipts = state.get("raw_receipts", [])

        for r in raw_receipts:

            file_id = r.get("file_id")
            raw_text = r.get("raw_text") or ""
            parsed = safe_load_json(r.get("parsed"))

            merchant = (
                parsed.get("vendor_store")
                or parsed.get("vendor")
                or parsed.get("store")
                or "Unknown"
            )

            date = parsed.get("date")

            items = parsed.get("items") or []
            total = 0.0
            for it in items:
                try:
                    total += float(it.get("price", 0))
                except:
                    pass
            total = round(total, 2)

            # ==========================================
            #  HYBRID CATEGORY DETECTION
            # ==========================================
            # 1) Try LLM
            ai_category = classify_category_llm(merchant, items, raw_text)

            # 2) Fallback → static rules
            static_cat = static_category_classifier((raw_text + merchant).lower())

            final_category = ai_category if ai_category else static_cat

            logger.info(f"[{file_id}] FINAL CATEGORY = {final_category}")

            extracted.append(
                {
                    "id": file_id,
                    "merchant": merchant,
                    "date": date,
                    "total": total,
                    "items": items,
                    "raw_text": raw_text,
                    "category": final_category,
                    "category_ai": ai_category,
                    "category_static": static_cat
                }
            )

        state["extracted"] = extracted
        return state
