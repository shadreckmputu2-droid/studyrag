"""Sliding-window chunker that prefers paragraph boundaries."""
import re
from dataclasses import dataclass, asdict

from .loader import Page


@dataclass
class Chunk:
    id: str
    source: str
    page: int
    text: str

    def to_dict(self) -> dict:
        return asdict(self)


def chunk_pages(pages: list[Page], max_words: int = 110, overlap: int = 25) -> list[Chunk]:
    if overlap >= max_words:
        raise ValueError("overlap must be smaller than max_words")
    chunks: list[Chunk] = []
    for pg in pages:
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", pg.text) if p.strip()]
        buf: list[str] = []
        n = 0

        def flush() -> None:
            nonlocal buf, n
            if not buf:
                return
            text = " ".join(buf).strip()
            chunks.append(Chunk(f"{pg.source}:{pg.page}:{len(chunks)}", pg.source, pg.page, text))
            tail = text.split()[-overlap:] if overlap else []
            buf, n = ([" ".join(tail)] if tail else []), len(tail)

        for para in paragraphs:
            words = para.split()
            if n + len(words) > max_words and n > overlap:
                flush()
            # a single huge paragraph: window it
            while len(words) > max_words:
                head, words = words[:max_words], words[max_words - overlap:]
                buf.append(" ".join(head))
                n += len(head)
                flush()
            buf.append(" ".join(words))
            n += len(words)
        if n > overlap or (buf and not chunks):
            flush()
    return chunks
