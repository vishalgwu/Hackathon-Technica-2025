import os
from typing import Any, Dict, List, Optional, Callable

from dotenv import load_dotenv
from openai import OpenAI

from .classification_agent import ClassificationAgent

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ----------------- Helper: simple risk mapping ----------------- #

def _risk_level_from_score(score: float) -> str:
    """
    Map numeric risk score (0–100) to label.
    """
    if score >= 75:
        return "HIGH"
    elif score >= 40:
        return "MEDIUM"
    else:
        return "LOW"


class ComplianceAgent:
    """
    Advanced Compliance Agent.

    - Uses:
        * Rule-based checks (amount, merchant, description)
        * ClassificationAgent for category
        * Optional RAG retriever for compliance docs (AML/KYC, bank policy)
        * LLM to generate natural language explanation

    - Public methods:
        * assess_transaction(tx, context_transactions=None)
        * assess_batch(transactions)
    """

    # Simple rule thresholds (you can tune)
    LARGE_AMOUNT_THRESHOLD = 1000.0
    VERY_LARGE_AMOUNT_THRESHOLD = 5000.0
    HIGH_RISK_MERCHANT_KEYWORDS = [
        "CRYPTO", "BINANCE", "COINBASE", "GAMBLING", "CASINO", "BET", "POKER",
        "FX", "FOREX", "BINARY OPTION",
    ]
    CASH_KEYWORDS = [
        "ATM", "CASH", "WITHDRAWAL",
    ]
    INTERNATIONAL_KEYWORDS = [
        "INTERNATIONAL", "INTL", "FX FEE",
    ]

    def __init__(
        self,
        retriever: Optional[Callable[[str], str]] = None,
        client_override: Optional[OpenAI] = None,
    ):
        """
        retriever: Optional function(question: str) -> str
            If provided, will be used to fetch RAG context from compliance docs
            (e.g. AML policy, bank rules, legal PDFs).
        """
        self.classifier = ClassificationAgent()
        self.client = client_override or client
        self.retriever = retriever

    # ----------------- PUBLIC API ----------------- #

    def assess_transaction(
        self,
        tx: Dict[str, Any],
        context_transactions: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Returns:
            {
                "category": str,
                "risk_score": float (0–100),
                "risk_level": "LOW" | "MEDIUM" | "HIGH",
                "flags": List[str],
                "explanation": str,
            }
        """

        description = (tx.get("description") or tx.get("narration") or "").upper()
        merchant = (tx.get("merchant") or "").upper()
        amount = float(tx.get("amount") or 0.0)

        # 1) Classify the transaction category (reuses our existing agent)
        category = self.classifier.classify_transaction(tx)

        # 2) Rule-based checks → accumulate risk points and flags
        risk_score, flags = self._apply_rules(
            amount=amount,
            description=description,
            merchant=merchant,
            category=category,
            context_transactions=context_transactions,
        )

        risk_level = _risk_level_from_score(risk_score)

        # 3) Optional RAG context (if a retriever is plugged in later)
        rag_context = ""
        if self.retriever is not None:
            question = (
                f"Bank compliance rules for transaction category {category}, "
                f"merchant '{merchant}', amount {amount}. "
                f"Focus on AML/KYC and suspicious activity indicators."
            )
            try:
                rag_context = self.retriever(question)
            except Exception:
                rag_context = ""

        # 4) Ask LLM for final explanation, using rules + optional RAG context
        explanation = self._generate_explanation(
            tx=tx,
            category=category,
            risk_score=risk_score,
            risk_level=risk_level,
            flags=flags,
            rag_context=rag_context,
        )

        return {
            "category": category,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "flags": flags,
            "explanation": explanation,
        }

    def assess_batch(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Assess a list of transactions. This allows us to use context such as
        repeated merchants, rapid small transactions, etc. if needed.
        """
        results = []
        for tx in transactions:
            result = self.assess_transaction(tx, context_transactions=transactions)
            results.append(result)
        return results

    # ----------------- INTERNAL: RULE ENGINE ----------------- #

    def _apply_rules(
        self,
        amount: float,
        description: str,
        merchant: str,
        category: str,
        context_transactions: Optional[List[Dict[str, Any]]] = None,
    ) -> (float, List[str]):
        """
        Apply rule-based checks and compute risk score.
        """

        score = 0.0
        flags: List[str] = []

        # Rule 1: Very large amount
        if amount >= self.VERY_LARGE_AMOUNT_THRESHOLD:
            score += 50
            flags.append("Very large transaction amount")

        # Rule 2: Large amount
        elif amount >= self.LARGE_AMOUNT_THRESHOLD:
            score += 25
            flags.append("Large transaction amount")

        text = f"{description} {merchant}"

        # Rule 3: High-risk merchants / activities
        for kw in self.HIGH_RISK_MERCHANT_KEYWORDS:
            if kw in text:
                score += 40
                flags.append(f"High-risk merchant or activity: {kw}")
                break

        # Rule 4: Cash / ATM
        for kw in self.CASH_KEYWORDS:
            if kw in text:
                score += 20
                flags.append("Cash / ATM related transaction")
                break

        # Rule 5: International charges
        for kw in self.INTERNATIONAL_KEYWORDS:
            if kw in text:
                score += 15
                flags.append("International / FX related transaction")
                break

        # Rule 6: Category-based risk
        if category in ["TRANSFER", "OTHER"]:
            score += 10
            flags.append(f"Ambiguous category: {category}")

        # Rule 7: Multiple similar transactions in context (e.g. smurfing)
        if context_transactions:
            similar_count = 0
            for other in context_transactions:
                if other is tx:
                    continue
                o_desc = (other.get("description") or "").upper()
                o_amount = float(other.get("amount") or 0.0)

                # Very rough heuristic: same merchant & similar amount
                if merchant and merchant != "" and merchant in (other.get("merchant") or "").upper():
                    if abs(o_amount - amount) < 5.0:
                        similar_count += 1

            if similar_count >= 3:
                score += 25
                flags.append("Multiple similar transactions (possible structuring)")

        # Cap score between 0 and 100
        score = max(0.0, min(100.0, score))

        # If no flags at all, keep risk low
        if not flags:
            score = 5.0

        return score, flags

    # ----------------- INTERNAL: LLM EXPLANATION ----------------- #

    def _generate_explanation(
        self,
        tx: Dict[str, Any],
        category: str,
        risk_score: float,
        risk_level: str,
        flags: List[str],
        rag_context: str,
    ) -> str:
        """
        Ask the LLM to produce a short, clear explanation combining:
        - rules that triggered
        - basic AML/compliance intuition
        - optional extra context from RAG
        """

        user_msg = f"""
        You are a bank compliance and AML assistant.

        Transaction:
            Description: {tx.get("description")}
            Merchant: {tx.get("merchant")}
            Amount: {tx.get("amount")}
            Category (model-assigned): {category}

        Risk score: {risk_score:.1f} (0–100)
        Risk level: {risk_level}
        Flags raised: {flags}

        Additional compliance context (may be empty):
        {rag_context}

        Explain in 3–5 sentences:
        - Why this transaction has this risk level
        - What the flags mean
        - Whether this looks like normal customer activity or something that might need review
        - Use simple, clear language suitable for a junior analyst.
        """

        completion = self.client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an experienced bank compliance officer. "
                        "Explain suspicion level clearly, but do not claim to make legal determinations."
                    ),
                },
                {"role": "user", "content": user_msg},
            ],
            temperature=0.2,
            max_tokens=250,
        )

        return completion.choices[0].message.content.strip()
