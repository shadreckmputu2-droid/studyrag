"""Run a case file against a RAG instance, summarise, and compare with a baseline."""
import json
import time
from pathlib import Path

from . import metrics as M

REGRESSION_TOLERANCE = 0.02
HIGHER_IS_BETTER = ["hit_at_k", "mrr", "keyword_coverage", "citation_validity", "abstention_accuracy", "faithfulness"]


def load_cases(path: str | Path) -> list[dict]:
    cases = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            cases.append(json.loads(line))
    return cases


def run_eval(rag, cases: list[dict], judge=None) -> dict:
    results = []
    for c in cases:
        ans = rag.ask(c["question"])
        answerable = c.get("answerable", True)
        row = {
            "id": c["id"],
            "question": c["question"],
            "answerable": answerable,
            "answer": ans.answer,
            "abstained": ans.abstained,
            "latency_ms": round(ans.latency_ms, 2),
            "abstention_correct": float(ans.abstained != answerable),
            "citation_valid": M.citation_valid(ans),
        }
        if answerable:
            flags = M.relevance_flags(ans.hits, c.get("gold_contains", []))
            row["hit_at_k"] = M.hit_at_k(flags)
            row["rr"] = M.reciprocal_rank(flags)
            row["keyword_coverage"] = M.keyword_coverage(ans.answer, c.get("keywords", []))
        if judge is not None and answerable:
            row["faithfulness"] = judge.faithful(ans)
        row["passed"] = _passed(row)
        results.append(row)

    ans_rows = [r for r in results if r["answerable"]]
    lat = [r["latency_ms"] for r in results]
    summary = {
        "n_cases": len(results),
        "hit_at_k": M.mean([r["hit_at_k"] for r in ans_rows]),
        "mrr": M.mean([r["rr"] for r in ans_rows]),
        "keyword_coverage": M.mean([r["keyword_coverage"] for r in ans_rows]),
        "citation_validity": M.mean([r["citation_valid"] for r in results]),
        "abstention_accuracy": M.mean([r["abstention_correct"] for r in results]),
        "latency_p50_ms": M.percentile(lat, 0.5),
        "latency_p95_ms": M.percentile(lat, 0.95),
    }
    if judge is not None:
        summary["faithfulness"] = M.mean([r["faithfulness"] for r in ans_rows if "faithfulness" in r])
    return {
        "meta": {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "mode": rag.mode,
            "k": rag.k,
            "llm": getattr(rag.llm, "name", "unknown"),
            "chunks": len(rag.chunks),
        },
        "summary": {k: round(v, 4) if isinstance(v, float) else v for k, v in summary.items()},
        "cases": results,
    }


def _passed(row: dict) -> bool:
    if not row["abstention_correct"] or not row["citation_valid"]:
        return False
    if row["answerable"]:
        return row.get("hit_at_k", 0) == 1.0 and row.get("keyword_coverage", 0) >= 0.5
    return True


def compare(current: dict, baseline: dict, tolerance: float = REGRESSION_TOLERANCE) -> dict:
    """Return per-metric deltas and the list of metrics that regressed beyond tolerance."""
    deltas, regressions = {}, []
    for m in HIGHER_IS_BETTER:
        if m in current["summary"] and m in baseline["summary"]:
            d = round(current["summary"][m] - baseline["summary"][m], 4)
            deltas[m] = d
            if d < -tolerance:
                regressions.append(m)
    base_pass = {c["id"] for c in baseline["cases"] if c["passed"]}
    newly_failing = [c["id"] for c in current["cases"] if not c["passed"] and c["id"] in base_pass]
    return {"deltas": deltas, "regressions": regressions, "newly_failing": newly_failing}


def save(result: dict, path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(result, indent=2), encoding="utf-8")
