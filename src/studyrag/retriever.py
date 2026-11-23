"""BM25 (no dependencies) + optional dense embeddings, fused with RRF."""
import math
import re
from collections import Counter
from dataclasses import dataclass

from .chunker import Chunk

STOP = set(
    "a an the of to in on for and or is are was were be by with as at it its this that from "
    "what which how why when does do did can use used using into than then also".split()
)


def tokenize(text: str) -> list[str]:
    text = text.lower().replace("'", "").replace("\u2019", "")  # don't -> dont, student's -> students
    tokens = re.findall(r"[a-z0-9]+", text)
    return [
        w for w in tokens
        if w not in STOP and (len(w) > 1 or w.isdigit() or w in {"d", "t", "s", "r"})
    ]


@dataclass
class Hit:
    chunk: Chunk
    score: float


class BM25:
    def __init__(self, docs: list[str], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.tok = [tokenize(d) for d in docs]
        self.tf = [Counter(t) for t in self.tok]
        self.n = len(docs)
        self.avgdl = (sum(len(t) for t in self.tok) / self.n) if self.n else 0.0
        self.df: Counter = Counter()
        for t in self.tok:
            self.df.update(set(t))

    def scores(self, query: str) -> list[float]:
        q = tokenize(query)
        out = [0.0] * self.n
        for i, tf in enumerate(self.tf):
            dl = len(self.tok[i]) or 1
            s = 0.0
            for w in q:
                f = tf.get(w, 0)
                if not f:
                    continue
                idf = math.log(1 + (self.n - self.df[w] + 0.5) / (self.df[w] + 0.5))
                s += idf * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * dl / self.avgdl))
            out[i] = s
        return out


class Dense:
    """Optional semantic retriever. Needs `pip install studyrag[dense]`."""

    def __init__(self, docs: list[str], model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(model)
        self.emb = self.model.encode(docs, normalize_embeddings=True)

    def scores(self, query: str) -> list[float]:
        q = self.model.encode([query], normalize_embeddings=True)[0]
        return (self.emb @ q).tolist()


class Retriever:
    def __init__(self, chunks: list[Chunk], mode: str = "bm25"):
        if mode not in {"bm25", "dense", "hybrid"}:
            raise ValueError("mode must be bm25, dense or hybrid")
        self.chunks, self.mode = chunks, mode
        docs = [c.text for c in chunks]
        self.bm25 = BM25(docs) if mode in {"bm25", "hybrid"} else None
        self.dense = Dense(docs) if mode in {"dense", "hybrid"} else None

    def search(self, query: str, k: int = 4) -> list[Hit]:
        if not self.chunks:
            return []
        if self.mode == "bm25":
            ranked = self._rank(self.bm25.scores(query))
        elif self.mode == "dense":
            ranked = self._rank(self.dense.scores(query))
        else:  # reciprocal rank fusion
            fused: Counter = Counter()
            for scorer in (self.bm25, self.dense):
                for rank, (i, _) in enumerate(self._rank(scorer.scores(query))[:20]):
                    fused[i] += 1 / (60 + rank)
            ranked = fused.most_common()
        return [Hit(self.chunks[i], float(s)) for i, s in ranked[:k] if s > 0]

    @staticmethod
    def _rank(scores: list[float]) -> list[tuple[int, float]]:
        return sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
