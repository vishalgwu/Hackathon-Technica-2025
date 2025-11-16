import re
import pandas as pd
from pathlib import Path
from .config import TEXT_DIR, STRUCTURED_DIR
from .logger import get_logger

logger = get_logger(__name__)

# Simple regex for finding dollar amounts
AMOUNT_PATTERN = re.compile(r"\b(\d+\.\d{2})\b")

def parse_text_file(text_path: Path) -> dict:
    text = text_path.read_text(encoding="utf-8")

    amounts = AMOUNT_PATTERN.findall(text)
    amount = max(map(float, amounts)) if amounts else None

    return {
        "file_id": text_path.stem,
        "amount": amount,
        "raw_text": text
    }


def run_parsing():
    STRUCTURED_DIR.mkdir(parents=True, exist_ok=True)

    records = []
    for txt_file in TEXT_DIR.glob("*.txt"):
        logger.info(f"Parsing {txt_file.name}")
        records.append(parse_text_file(txt_file))

    df = pd.DataFrame(records)
    out_path = STRUCTURED_DIR / "expenses.parquet"
    df.to_parquet(out_path, index=False)

    logger.info(f"Saved structured dataset -> {out_path}")


if __name__ == "__main__":
    run_parsing()
