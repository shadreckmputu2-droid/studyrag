"""Pure metric functions. No I/O, easy to unit test."""
import statistics


def relevance_flags(hits, gold_contains: list[str]) -> list[bool]:
    """A retrieved chunk is relevant if it contains any gold phrase (robust to re-chunking)."""
    gold = [g.lower() for g in gold_contains]
    return [any(g in h.chunk.text.lower() for g in gold) for h in hits]


def hit_at_k(flags: list[bool]) -> float:
    return 1.0 if any(flags) else 0.0


def reciprocal_rank(flags: list[bool]) -> float:
    return 1.0 / (flags.index(True) + 1) if True in flags else 0.0


def keyword_coverage(answer: str, keywords: list[str]) -> float:
    if not keywords:
        return 1.0
    a = answer.lower()
    return sum(k.lower() in a for k in keywords) / len(keywords)


def citation_valid(answer_obj) -> float:
    """Answered responses must cite at least one real source and never cite a non-existent one."""
    if answer_obj.abstained:
        return 1.0
    return 1.0 if answer_obj.citations and not answer_obj.invalid_citations else 0.0


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    return s[min(len(s) - 1, int(round(p * (len(s) - 1))))]


def mean(values: list[float]) -> float:
    return statistics.fmean(values) if values else 0.0
