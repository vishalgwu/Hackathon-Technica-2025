import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from openai import OpenAI

from .classification_agent import ClassificationAgent
from .tax_agent import TaxAgent
from .compliance_agent import ComplianceAgent
from .summary_agent import SummaryAgent

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class DispatcherAgent:
    """
    Advanced Multi-Agent Dispatcher.

    Supports multiple intents:
        - Spending summary
        - Tax deduction analysis
        - Compliance / suspicious activity analysis
        - Transaction classification
        - Combined queries (multi-intent)
        - General financial questions

    API:
        analyze(query: str, transactions: List[Dict], tx: Optional[Dict]) -> Dict
    """

    def __init__(self, client_override: Optional[OpenAI] = None):
        self.client = client_override or client

        # worker agents
        self.classifier = ClassificationAgent()
        self.tax_agent = TaxAgent()
        self.compliance_agent = ComplianceAgent()
        self.summary_agent = SummaryAgent()

    # -----------------------------------------------------
    # 🔥 MAIN ENTRY
    # -----------------------------------------------------

    def analyze(
        self,
        query: str,
        transactions: Optional[List[Dict[str, Any]]] = None,
        single_tx: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Main routing function.

        Parameters:
        - query: user natural language question
        - transactions: full list of transactions (for summaries)
        - single_tx: one specific transaction (for tax/compliance/classifier)

        Returns a structured dict:
        {
            "intents": [...],
            "results": {
                "summary": {...},
                "tax": {...},
                "compliance": {...},
                "classification": {...},
            }
        }
        """

        # Step 1: Determine INTENTS using an LLM
        intents = self._detect_intents(query)

        results = {
            "summary": None,
            "tax": None,
            "compliance": None,
            "classification": None,
            "raw_llm": None,
        }

        # Step 2: Execute all required agents
        if "SUMMARY" in intents:
            if not transactions:
                results["summary"] = {"error": "No transactions provided"}
            else:
                results["summary"] = self.summary_agent.summarize(transactions)

        if "TAX" in intents:
            if not single_tx:
                results["tax"] = {"error": "No transaction provided for tax analysis"}
            else:
                results["tax"] = self.tax_agent.analyze_transaction(single_tx)

        if "COMPLIANCE" in intents:
            if not single_tx:
                results["compliance"] = {"error": "No transaction provided for compliance"}
            else:
                results["compliance"] = self.compliance_agent.assess_transaction(single_tx)

        if "CATEGORY" in intents:
            if not single_tx:
                results["classification"] = {"error": "No transaction provided for classification"}
            else:
                results["classification"] = self.classifier.classify_transaction(single_tx)

        # Step 3: For fully unknown queries → fallback to LLM
        if intents == ["UNKNOWN"]:
            results["raw_llm"] = self._fallback_llm(query)

        return {
            "intents": intents,
            "results": results,
        }

    # -----------------------------------------------------
    # 🔍 INTENT DETECTION
    # -----------------------------------------------------

    def _detect_intents(self, query: str) -> List[str]:
        """
        Returns multiple intents:
            SUMMARY
            TAX
            COMPLIANCE
            CATEGORY
            UNKNOWN
        """

        user_msg = f"""
        Classify this user question into one or more intents:

        "{query}"

        Possible intents:
        - SUMMARY: Spending totals, categories, months
        - TAX: Deductible? tax calculation? IRS?
        - COMPLIANCE: suspicious? risky? fraud? compliance?
        - CATEGORY: classify transaction? what category?
        - UNKNOWN: general conversation

        Return a JSON list of intents. No explanation, ONLY the list.
        """

        completion = self.client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an intent classifier. Respond with ONLY a JSON list of intents.",
                },
                {"role": "user", "content": user_msg},
            ],
            temperature=0,
            max_tokens=100,
        )

        raw = completion.choices[0].message.content.strip()

        # Very safe parsing
        raw = raw.replace("'", '"')  # fix JSON single quotes if any
        try:
            import json
            intents = json.loads(raw)
        except Exception:
            intents = ["UNKNOWN"]

        # Ensure it's a list
        if not isinstance(intents, list):
            intents = ["UNKNOWN"]

        return intents

    # -----------------------------------------------------
    # 🧠 FALLBACK LLM (for unknown queries)
    # -----------------------------------------------------

    def _fallback_llm(self, query: str) -> str:
        completion = self.client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "You are a helpful finance assistant."},
                {"role": "user", "content": query},
            ],
            temperature=0.3,
            max_tokens=300,
        )
        return completion.choices[0].message.content.strip()
