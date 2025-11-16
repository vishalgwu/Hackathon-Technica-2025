import os
import re
import json
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Reuse the same API key style you used in extraction_agent.py
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Canonical categories we will use across the whole project
CANONICAL_CATEGORIES = [
    "TRAVEL",
    "MEALS",
    "GROCERIES",
    "RENT",
    "ENTERTAINMENT",
    "ELECTRONICS",
    "HEALTH",
    "UTILITIES",
    "INCOME",
    "TRANSFER",
    "OTHER",
]

# Simple keyword rules to avoid calling the LLM for obvious cases
KEYWORD_RULES = {
    # Travel
    "UBER": "TRAVEL",
    "LYFT": "TRAVEL",
    "DELTA": "TRAVEL",
    "UNITED": "TRAVEL",
    "AMTRAK": "TRAVEL",
    "AIRLINES": "TRAVEL",
    "HOTEL": "TRAVEL",
    "MARRIOTT": "TRAVEL",
    "HILTON": "TRAVEL",

    # Meals / Restaurants
    "STARBUCKS": "MEALS",
    "MCDONALD": "MEALS",
    "BURGER KING": "MEALS",
    "UBER EATS": "MEALS",
    "DOORDASH": "MEALS",
    "GRUBHUB": "MEALS",
    "RESTAURANT": "MEALS",
    "CAFE": "MEALS",

    # Groceries
    "WHOLE FOODS": "GROCERIES",
    "WALMART": "GROCERIES",
    "SAFEWAY": "GROCERIES",
    "TRADER JOE": "GROCERIES",
    "KROGER": "GROCERIES",

    # Electronics / Shopping
    "BEST BUY": "ELECTRONICS",
    "APPLE.COM/BILL": "ELECTRONICS",
    "APPLE STORE": "ELECTRONICS",
    "AMAZON": "ELECTRONICS",
    "MICRO CENTER": "ELECTRONICS",

    # Utilities
    "VERIZON": "UTILITIES",
    "COMCAST": "UTILITIES",
    "ATT": "UTILITIES",
    "AT&T": "UTILITIES",
    "T-MOBILE": "UTILITIES",

    # Rent / Housing
    "APARTMENTS": "RENT",
    "LEASE": "RENT",
    "ZILLOW": "RENT",

    # Health
    "CVS": "HEALTH",
    "WALGREENS": "HEALTH",
    "PHARMACY": "HEALTH",
    "HOSPITAL": "HEALTH",
    "DENTAL": "HEALTH",

    # Income / transfer
    "PAYROLL": "INCOME",
    "DIRECT DEP": "INCOME",
    "VENMO": "TRANSFER",
    "ZELLE": "TRANSFER",
    "CASH APP": "TRANSFER",
}


class ClassificationAgent:
    """
    Classifies individual transactions into high-level categories.
    First uses keyword rules; if no match, falls back to the LLM.
    """

    def __init__(self, client_override: Optional[OpenAI] = None):
        self.client = client_override or client

    # -------------- Public API --------------

    def classify_transaction(self, tx: Dict[str, Any]) -> str:
        """
        tx is a dict with (ideally) at least:
        - description (str)
        - merchant   (str, optional)
        - amount     (float, optional)

        Returns a single category from CANONICAL_CATEGORIES.
        """

        description = (tx.get("description") or tx.get("narration") or "").upper()
        merchant = (tx.get("merchant") or "").upper()

        # 1) Try rule-based classification first
        rule_category = self._apply_keyword_rules(description, merchant)
        if rule_category:
            return rule_category

        # 2) If still unknown, ask the LLM (few-shot classification)
        return self._classify_with_llm(description=description, merchant=merchant, amount=tx.get("amount"))

    def classify_transactions_batch(self, rows: List[Dict[str, Any]]) -> List[str]:
        """
        Convenience method if you want to classify a list of transactions.
        """
        return [self.classify_transaction(tx) for tx in rows]

    # -------------- Internal helpers --------------

    def _apply_keyword_rules(self, description: str, merchant: str) -> Optional[str]:
        text = f"{description} {merchant}"

        for keyword, category in KEYWORD_RULES.items():
            if keyword in text:
                return category

        return None

    def _classify_with_llm(self, description: str, merchant: str, amount: Optional[float]) -> str:
        """
        Uses the OpenAI model as a fallback to classify the transaction.
        We keep it simple: model returns exactly one of the allowed categories.
        """

        # Build a compact prompt
        user_text = f"""
        Description: {description}
        Merchant: {merchant or "N/A"}
        Amount: {amount if amount is not None else "N/A"}

        Choose the single best category from this list:
        {", ".join(CANONICAL_CATEGORIES)}

        Answer with ONLY the category name, nothing else.
        """

        completion = self.client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a financial transaction classification assistant. "
                        "You MUST respond with exactly one category name from the allowed list."
                    ),
                },
                {"role": "user", "content": user_text},
            ],
            temperature=0.0,
            max_tokens=10,
        )

        category_raw = completion.choices[0].message.content.strip().upper()

        # Simple clean-up in case the model adds extra text
        # Example: "Category: MEALS" -> "MEALS"
        for cat in CANONICAL_CATEGORIES:
            if cat in category_raw:
                return cat

        # If model returns something unexpected, fall back to OTHER
        return "OTHER"
