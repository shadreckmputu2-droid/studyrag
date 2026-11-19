"""Load .txt / .md / .pdf files into page-level text."""
from dataclasses import dataclass
from pathlib import Path

SUPPORTED = {".txt", ".md", ".pdf"}


@dataclass
class Page:
    source: str
    page: int
    text: str


def load_path(path: str | Path) -> list[Page]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"{p} does not exist")
    files = [p] if p.is_file() else sorted(f for f in p.rglob("*") if f.suffix.lower() in SUPPORTED)
    pages: list[Page] = []
    for f in files:
        if f.suffix.lower() == ".pdf":
            from pypdf import PdfReader

            for i, pg in enumerate(PdfReader(str(f)).pages, 1):
                text = (pg.extract_text() or "").strip()
                if text:
                    pages.append(Page(f.name, i, text))
        elif f.suffix.lower() in SUPPORTED:
            text = f.read_text(encoding="utf-8", errors="ignore").strip()
            if text:
                pages.append(Page(f.name, 1, text))
    return pages
