import os
import pandas as pd
from typing import List, Dict

STRUCTURED_PATH = "data/structured/expenses.parquet"

def load_structured_receipts() -> List[Dict]:
    if not os.path.exists(STRUCTURED_PATH):
        print(f"❌ Structured parquet file not found: {STRUCTURED_PATH}")
        return []

    try:
        df = pd.read_parquet(STRUCTURED_PATH)
    except Exception as e:
        print(f"❌ Failed to load parquet file: {e}")
        return []

    # Convert DataFrame rows to list of dicts
    records = df.to_dict(orient="records")
    return records
