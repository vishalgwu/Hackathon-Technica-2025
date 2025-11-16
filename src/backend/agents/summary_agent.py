import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from openai import OpenAI
import pandas as pd

from .classification_agent import ClassificationAgent

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class SummaryAgent:
    """
    Finance Summary Agent

    Input: list of transaction dicts, e.g.:
        {
          "date": "2024-05-01",
          "description": "UBER TRIP",
          "merchant": "UBER",
          "amount": -23.45,
          "category": "TRAVEL"  # optional; if missing, we classify
        }

    Output: charts-ready analytics + LLM narrative, e.g.:
        {
          "monthly_totals": [...],
          "category_totals": [...],
          "merchant_totals": [...],
          "unusual_transactions": [...],
          "summary_text": "Natural language summary..."
        }
    """

    def __init__(self, client_override: Optional[OpenAI] = None):
        self.client = client_override or client
        self.classifier = ClassificationAgent()

    # -------------- PUBLIC API --------------

    def summarize(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Main entrypoint.
        """
        if not transactions:
            return {
                "monthly_totals": [],
                "category_totals": [],
                "merchant_totals": [],
                "unusual_transactions": [],
                "summary_text": "No transactions available to summarize.",
            }

        df = pd.DataFrame(transactions).copy()

        # Ensure amount is numeric
        if "amount" not in df.columns:
            raise ValueError("Each transaction must have an 'amount' field.")

        df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
        df = df.dropna(subset=["amount"])

        # Normalize column names we will use
        if "date" in df.columns:
            date_col = "date"
        elif "transaction_date" in df.columns:
            date_col = "transaction_date"
        else:
            date_col = None  # no dates, so no monthly grouping

        if "merchant" not in df.columns:
            df["merchant"] = df.get("description", "")

        # Ensure category exists; if not, classify row by row
        if "category" not in df.columns:
            df["category"] = df.apply(
                lambda row: self.classifier.classify_transaction(row.to_dict()),
                axis=1,
            )

        # 1) Monthly totals
        monthly_totals = self._compute_monthly_totals(df, date_col)

        # 2) Category totals
        category_totals = self._compute_category_totals(df)

        # 3) Merchant totals (top N)
        merchant_totals = self._compute_merchant_totals(df, top_n=10)

        # 4) Unusual spending
        unusual = self._detect_unusual_spend(df, date_col)

        # 5) LLM summary
        summary_text = self._generate_summary_text(
            monthly_totals=monthly_totals,
            category_totals=category_totals,
            merchant_totals=merchant_totals,
            unusual_transactions=unusual,
        )

        return {
            "monthly_totals": monthly_totals,
            "category_totals": category_totals,
            "merchant_totals": merchant_totals,
            "unusual_transactions": unusual,
            "summary_text": summary_text,
        }

    # -------------- INTERNAL: ANALYTICS --------------

    def _compute_monthly_totals(
        self,
        df: pd.DataFrame,
        date_col: Optional[str],
    ) -> List[Dict[str, Any]]:
        if not date_col:
            return []

        dates = pd.to_datetime(df[date_col], errors="coerce")
        df = df.assign(_month=dates.dt.to_period("M").astype(str))
        monthly = (
            df.groupby("_month", as_index=False)["amount"]
            .sum()
            .rename(columns={"_month": "month", "amount": "total_amount"})
            .sort_values("month")
        )

        return monthly.to_dict(orient="records")

    def _compute_category_totals(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        cat = (
            df.groupby("category", as_index=False)["amount"]
            .sum()
            .rename(columns={"amount": "total_amount"})
            .sort_values("total_amount")
        )
        return cat.to_dict(orient="records")

    def _compute_merchant_totals(
        self,
        df: pd.DataFrame,
        top_n: int = 10,
    ) -> List[Dict[str, Any]]:
        mer = (
            df.groupby("merchant", as_index=False)["amount"]
            .sum()
            .rename(columns={"amount": "total_amount"})
        )

        # Sort by absolute spend descending
        mer["abs_amount"] = mer["total_amount"].abs()
        mer = mer.sort_values("abs_amount", ascending=False).head(top_n)
        mer = mer.drop(columns=["abs_amount"])

        return mer.to_dict(orient="records")

    def _detect_unusual_spend(
        self,
        df: pd.DataFrame,
        date_col: Optional[str],
    ) -> List[Dict[str, Any]]:
        """
        Very simple anomaly heuristic:
        - Flag transactions whose |amount| > mean + 2*std of |amount|.
        """
        if df.empty:
            return []

        amounts = df["amount"].abs()
        mean = amounts.mean()
        std = amounts.std(ddof=0) if amounts.size > 1 else 0.0

        threshold = mean + 2 * std
        mask = amounts > threshold

        if not mask.any():
            return []

        unusual = df.loc[mask, ["date", "transaction_date", "description", "merchant", "amount", "category"]].copy()

        # Normalize date column in output
        if date_col and date_col in unusual.columns:
            unusual["date"] = unusual[date_col]
        elif "date" not in unusual.columns and "transaction_date" in unusual.columns:
            unusual["date"] = unusual["transaction_date"]

        # Choose output columns
        cols = ["date", "description", "merchant", "amount", "category"]
        existing_cols = [c for c in cols if c in unusual.columns]

        unusual = unusual[existing_cols]

        return unusual.to_dict(orient="records")

    # -------------- INTERNAL: LLM SUMMARY --------------

    def _generate_summary_text(
        self,
        monthly_totals: List[Dict[str, Any]],
        category_totals: List[Dict[str, Any]],
        merchant_totals: List[Dict[str, Any]],
        unusual_transactions: List[Dict[str, Any]],
    ) -> str:
        """
        Use the LLM to produce a concise narrative based on precomputed stats.
        """

        # Build a compact, serializable view for the model
        analytics = {
            "monthly_totals": monthly_totals,
            "category_totals": category_totals,
            "merchant_totals": merchant_totals,
            "unusual_transactions": unusual_transactions[:10],
        }

        user_msg = f"""
        You are a financial analyst. You are given aggregated spending analytics in JSON-like form:

        {analytics}

        Write a concise, human-friendly summary (1–2 short paragraphs) plus 3–5 bullet-point insights. Cover:
        - Overall spending trend over time (rising, falling, stable)
        - Which categories and merchants dominate spending
        - Any unusual or outlier transactions
        - Simple recommendations (e.g., where to cut costs)

        Keep the tone clear and non-technical, suitable for a busy professional.
        """

        completion = self.client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful financial analyst. "
                        "Explain clearly and briefly, focusing on actionable insights."
                    ),
                },
                {"role": "user", "content": user_msg},
            ],
            temperature=0.3,
            max_tokens=400,
        )

        return completion.choices[0].message.content.strip()
