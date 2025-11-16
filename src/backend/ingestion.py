from pathlib import Path
from pypdf import PdfReader
from .config import RAW_PDF_DIR, TEXT_DIR
from .logger import get_logger

logger = get_logger(__name__)

def extract_text_from_pdf(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    pages_text = []

    for page in reader.pages:
        txt = page.extract_text() or ""
        pages_text.append(txt)

    return "\n\n".join(pages_text)


def run_ingestion():
    TEXT_DIR.mkdir(parents=True, exist_ok=True)

    for pdf_file in RAW_PDF_DIR.glob("*.pdf"):
        logger.info(f"Extracting text from {pdf_file.name}")
        text = extract_text_from_pdf(pdf_file)

        out_path = TEXT_DIR / f"{pdf_file.stem}.txt"
        out_path.write_text(text, encoding="utf-8")

        logger.info(f"Saved extracted text: {out_path}")


if __name__ == "__main__":
    run_ingestion()
