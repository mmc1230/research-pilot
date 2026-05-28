from pathlib import Path

from langchain_core.documents import Document
from pypdf import PdfReader


SECTION_NAMES = {
    "abstract": "Abstract",
    "introduction": "Introduction",
    "method": "Method",
    "methodology": "Method",
    "methods": "Method",
    "experiment": "Experiment",
    "experiments": "Experiment",
    "results": "Results",
    "conclusion": "Conclusion",
    "conclusions": "Conclusion",
}


def detect_section(text: str) -> str | None:
    stripped = text.strip().lower().strip(":")
    if len(stripped) > 80:
        return None
    for key, label in SECTION_NAMES.items():
        if stripped == key or stripped.startswith(f"{key} "):
            return label
    return None


def load_pdf(path: Path | str) -> list[Document]:
    pdf_path = Path(path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    reader = PdfReader(str(pdf_path))
    docs: list[Document] = []
    current_section = None
    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        for line in text.splitlines():
            section = detect_section(line)
            if section:
                current_section = section
                break
        if text.strip():
            docs.append(
                Document(
                    page_content=text,
                    metadata={
                        "source": str(pdf_path),
                        "filename": pdf_path.name,
                        "page": page_number,
                        "section": current_section,
                        "doc_type": "paper",
                    },
                )
            )
    if not docs:
        raise ValueError(f"No extractable text found in PDF: {pdf_path}")
    return docs


def load_text(path: Path | str, doc_type: str = "text") -> list[Document]:
    text_path = Path(path)
    if not text_path.exists():
        raise FileNotFoundError(f"Text file not found: {text_path}")
    text = text_path.read_text(encoding="utf-8", errors="ignore")
    return [
        Document(
            page_content=text,
            metadata={
                "source": str(text_path),
                "filename": text_path.name,
                "doc_type": doc_type,
            },
        )
    ]
