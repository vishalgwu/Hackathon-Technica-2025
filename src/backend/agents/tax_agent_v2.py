import os
from typing import Dict, Any, Optional

from dotenv import load_dotenv
from openai import OpenAI

from .classification_agent import ClassificationAgent

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class TaxAgent:
    """
    Full Tax Intelligence Agent:
    - Uses ClassificationAgent to get category
    - Calculates deduction percentage based on business rules
    - (Later) Uses RAG with IRS Publications 463/535
    """

    # Deduction rules (phase 1)
    DEDUCTION_RULES = {
        "MEALS": 0.50,         # IRS standard
        "TRAVEL": 1.00,        # business travel
        "ELECTRONICS": 0.30,   # simplified depreciation assumption
        "HEALTH": 0.00,        # personal, not deductible
        "GROCERIES": 0.00,     # not deductible
        "ENTERTAINMENT": 0.00, # entertainment mostly non-deductible
        "RENT": 0.00,          # unless home-office (not handled yet)
        "INCOME": 0.00,
        "TRANSFER": 0.00,
        "UTILITIES": 0.00,
        "OTHER": 0.00,
    }

    def __init__(self):
        self.classifier = ClassificationAgent()
        self.client = client

    # -------------- MAIN PUBLIC METHOD --------------

    def analyze_transaction(self, tx: Dict[str, Any]) -> Dict[str, Any]:
        """
        Returns a structured deduction analysis:
        - category
        - deduction %
        - deductible amount
        - explanation from LLM
        """

        # 1. Classify transaction category
        category = self.classifier.classify_transaction(tx)

        # 2. Get deduction rule
        deduction_pct = self.DEDUCTION_RULES.get(category, 0.0)

        amount = float(tx.get("amount", 0.0))
        deductible_amount = round(amount * deduction_pct, 2)

        # 3. Ask LLM for explanation (explain IRS logic)
        explanation = self._explain_deduction(category, amount, deductible_amount)

        return {
            "category": category,
            "amount": amount,
            "deduction_percentage": deduction_pct,
            "deductible_amount": deductible_amount,
            "explanation": explanation,
        }

    # -------------- INTERNAL -- LLM LOGIC --------------

    def _explain_deduction(self, category: str, amount: float, deductible: float) -> str:
        """
        Asks the LLM to provide a short, correct explanation.
        Later we will add RAG references to IRS documents.
        """

        user_msg = f"""
        Category: {category}
        Amount: {amount}
        Deductible: {deductible}

        Explain in 2–3 sentences why this category receives this deduction percentage
        based on common IRS business expense rules. Do NOT mention IRS section numbers yet.
        """

        completion = self.client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a tax deduction assistant. "
                        "Explain deduction rules clearly and simply."
                    ),
                },
                {"role": "user", "content": user_msg},
            ],
            temperature=0.2,
            max_tokens=200,
        )

        return completion.choices[0].message.content.strip()
