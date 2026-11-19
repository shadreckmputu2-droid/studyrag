"""Optional LLM-as-judge faithfulness check (needs ANTHROPIC_API_KEY)."""
import json
import os
import re

PROMPT = """You are grading a study assistant for faithfulness.
Sources:
{sources}

Answer to grade:
{answer}

Is EVERY factual claim in the answer supported by the sources? Reply with JSON only:
{{"supported": true|false, "reason": "<one short sentence>"}}"""


class Judge:
    def __init__(self, model: str | None = None):
        import anthropic

        self.client = anthropic.Anthropic()
        self.model = model or os.getenv("STUDYRAG_JUDGE_MODEL", "claude-sonnet-5-5")

    def faithful(self, answer_obj) -> float:
        if answer_obj.abstained:
            return 1.0
        sources = "\n\n".join(f"[{i}] {h.chunk.text}" for i, h in enumerate(answer_obj.hits, 1))
        msg = self.client.messages.create(
            model=self.model,
            max_tokens=200,
            messages=[{"role": "user", "content": PROMPT.format(sources=sources, answer=answer_obj.answer)}],
        )
        text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
        m = re.search(r"\{.*\}", text, re.S)
        try:
            return 1.0 if json.loads(m.group(0)).get("supported") else 0.0
        except (AttributeError, ValueError):
            return 0.0
