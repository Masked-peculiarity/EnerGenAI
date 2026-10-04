"""Local text extraction for user-provided knowledge documents."""

from io import BytesIO
from pathlib import Path

import pdfplumber


def extract_document_text(filename: str, content: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix in {".txt", ".md"}:
        return content.decode("utf-8-sig", errors="replace")
    if suffix == ".pdf":
        with pdfplumber.open(BytesIO(content)) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    raise ValueError("Only PDF, TXT, and Markdown files are supported")
