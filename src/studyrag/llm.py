"""Answer generators. Uses Claude when a key is set, otherwise an offline extractive fallback."""
import os
import re

from .retriever import Hit, tokenize

SYSTEM = (
    "You are a study assistant. Answer ONLY from the numbered sources provided. "
    "Cite every claim with its source number like [1] or [2]. "
    "If the sources do not contain the answer, reply exactly: I don't know based on the notes."
)

ABSTAIN = "I don't know based on the notes."


def build_prompt(question: str, hits: list[Hit]) -> str:
    srcs = "\n\n".join(
        f"[{i}] ({h.chunk.source}, p.{h.chunk.page})\n{h.chunk.text}"
        for i, h in enumerate(hits, 1)
    )
    return f"Sources:\n{srcs}\n\nQuestion: {question}"


class ExtractiveLLM:
    """No API needed: returns the most relevant sentences from the top sources, with citations."""

    name = "extractive"

    def generate(self, question: str, hits: list[Hit]) -> str:
        q = set(tokenize(question))
        scored = []

        for i, h in enumerate(hits, 1):
            for s in re.split(r"(?<=[.!?])\s+|\n+", h.chunk.text):
                overlap = len(q & set(tokenize(s)))
                if overlap:
                    scored.append((overlap, -i, s.strip(), i))

        if not scored:
            return ABSTAIN

        scored.sort(reverse=True)
        best_score = scored[0][0]

        out, seen = [], set()
        for overlap, _, sent, i in scored:
            if overlap / best_score < 0.8:
                continue

            if sent not in seen:  # overlapping chunks repeat sentences
                seen.add(sent)
                out.append(f"{sent} [{i}]")

            if len(out) == 2:
                break

        return " ".join(out)


class AnthropicLLM:
    def __init__(self, model: str | None = None):
        import anthropic

        self.client = anthropic.Anthropic()
        self.model = model or os.getenv("STUDYRAG_MODEL", "claude-sonnet-5-5")
        self.name = self.model

    def generate(self, question: str, hits: list[Hit]) -> str:
        msg = self.client.messages.create(
            model=self.model,
            max_tokens=600,
            system=SYSTEM,
            messages=[{"role": "user", "content": build_prompt(question, hits)}],
        )
        return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip()


def get_llm(kind: str = "auto"):
    if kind == "extractive":
        return ExtractiveLLM()
    if kind in {"auto", "claude"} and os.getenv("ANTHROPIC_API_KEY"):
        try:
            return AnthropicLLM()
        except ImportError:
            if kind == "claude":
                raise
    elif kind == "claude":
        raise RuntimeError("Set ANTHROPIC_API_KEY to use the Claude backend")
    return ExtractiveLLM()