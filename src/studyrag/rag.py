"""The RAG pipeline: ingest -> retrieve -> guard -> generate -> verify citations."""
import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

from .chunker import Chunk, chunk_pages
from .llm import ABSTAIN, get_llm
from .loader import load_path
from .retriever import Hit, Retriever, tokenize


@dataclass
class Answer:
    question: str
    answer: str
    abstained: bool
    citations: list[dict] = field(default_factory=list)
    hits: list[Hit] = field(default_factory=list)
    latency_ms: float = 0.0
    invalid_citations: list[int] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "question": self.question,
            "answer": self.answer,
            "abstained": self.abstained,
            "citations": self.citations,
            "invalid_citations": self.invalid_citations,
            "latency_ms": round(self.latency_ms, 1),
        }


class RAG:
    def __init__(self, index_dir: str = ".studyrag", mode: str = "bm25", llm: str = "auto", k: int = 4, min_score: float = 0.5, min_coverage: float = 0.4):
        self.index_dir, self.mode, self.k, self.min_score, self.min_coverage = Path(index_dir), mode, k, min_score, min_coverage
        self.llm = get_llm(llm)
        self.chunks: list[Chunk] = []
        self.retriever: Retriever | None = None

    # ---- ingestion -------------------------------------------------------
    def ingest(self, path: str, max_words: int = 110, overlap: int = 25) -> int:
        self.chunks = chunk_pages(load_path(path), max_words, overlap)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        (self.index_dir / "chunks.json").write_text(json.dumps([c.to_dict() for c in self.chunks]), encoding="utf-8")
        self.retriever = Retriever(self.chunks, self.mode)
        return len(self.chunks)

    def load(self) -> None:
        f = self.index_dir / "chunks.json"
        if not f.exists():
            raise FileNotFoundError(f"No index at {f}. Run: studyrag ingest <path>")
        self.chunks = [Chunk(**d) for d in json.loads(f.read_text(encoding="utf-8"))]
        self.retriever = Retriever(self.chunks, self.mode)

    @staticmethod
    def _coverage(question: str, hits: list[Hit]) -> float:
        """Share of the question's key terms found in the retrieved text.
        One shared word (e.g. 'algorithm') is not enough evidence to answer."""
        q = set(tokenize(question))
        if not q:
            return 0.0
        seen = set().union(*(set(tokenize(h.chunk.text)) for h in hits))
        return len(q & seen) / len(q)

    # ---- querying --------------------------------------------------------
    def ask(self, question: str) -> Answer:
        if self.retriever is None:
            self.load()
        t0 = time.perf_counter()
        hits = self.retriever.search(question, self.k)
        # guardrail: don't spend tokens (or hallucinate) when retrieval found nothing useful
        if not hits or hits[0].score < self.min_score or self._coverage(question, hits) < self.min_coverage:
            return Answer(question, ABSTAIN, True, hits=hits, latency_ms=(time.perf_counter() - t0) * 1000)
        text = self.llm.generate(question, hits)
        abstained = text.strip().lower().startswith("i don't know")
        cited = sorted({int(n) for n in re.findall(r"\[(\d+)\]", text)})
        invalid = [n for n in cited if not 1 <= n <= len(hits)]
        citations = [
            {"n": n, "source": hits[n - 1].chunk.source, "page": hits[n - 1].chunk.page, "snippet": hits[n - 1].chunk.text[:200]}
            for n in cited
            if 1 <= n <= len(hits)
        ]
        return Answer(question, text, abstained, citations, hits, (time.perf_counter() - t0) * 1000, invalid)
