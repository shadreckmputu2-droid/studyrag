import argparse
import json
import sys
from pathlib import Path

from .rag import RAG


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="studyrag", description="RAG study assistant + evaluation harness")
    p.add_argument("--index", default=".studyrag", help="index directory")
    p.add_argument("--mode", default="bm25", choices=["bm25", "dense", "hybrid"])
    p.add_argument("--llm", default="auto", choices=["auto", "claude", "extractive"])
    p.add_argument("-k", type=int, default=4)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("ingest", help="index a file or folder of .txt/.md/.pdf")
    s.add_argument("path")
    s = sub.add_parser("ask", help="ask one question")
    s.add_argument("question")
    s.add_argument("--json", action="store_true")
    s = sub.add_parser("serve", help="run the web API (needs studyrag[api])")
    s.add_argument("--port", type=int, default=8000)
    s = sub.add_parser("eval", help="evaluate against a case file")
    s.add_argument("--cases", default="evals/cases.jsonl")
    s.add_argument("--baseline", default="evals/baseline.json")
    s.add_argument("--report", default="evals/report.html")
    s.add_argument("--update-baseline", action="store_true")
    s.add_argument("--fail-on-regression", action="store_true")
    s.add_argument("--judge", action="store_true", help="LLM-as-judge faithfulness (needs API key)")
    a = p.parse_args(argv)

    rag = RAG(a.index, a.mode, a.llm, a.k)
    if a.cmd == "ingest":
        print(f"Indexed {rag.ingest(a.path)} chunks into {a.index}/")
    elif a.cmd == "ask":
        ans = rag.ask(a.question)
        if a.json:
            print(json.dumps(ans.to_dict(), indent=2))
        else:
            print(ans.answer)
            for c in ans.citations:
                print(f"  [{c['n']}] {c['source']} p.{c['page']}")
    elif a.cmd == "serve":
        from .api import serve

        serve(rag, a.port)
    elif a.cmd == "eval":
        return _eval(rag, a)
    return 0


def _eval(rag: RAG, a) -> int:
    from .evals import compare, load_cases, run_eval
    from .evals.report import render
    from .evals.runner import save

    judge = None
    if a.judge:
        from .evals.judge import Judge

        judge = Judge()
    rag.load()
    result = run_eval(rag, load_cases(a.cases), judge)
    cmp = None
    if Path(a.baseline).exists() and not a.update_baseline:
        cmp = compare(result, json.loads(Path(a.baseline).read_text(encoding="utf-8")))
    Path(a.report).parent.mkdir(parents=True, exist_ok=True)
    from .evals.report import render as _r

    Path(a.report).write_text(_r(result, cmp), encoding="utf-8")
    save(result, "evals/runs/latest.json")
    if a.update_baseline:
        save(result, a.baseline)
        print(f"Baseline updated: {a.baseline}")

    print(f"{result['meta']['mode']} | {result['meta']['llm']} | {result['summary']['n_cases']} cases")
    for k, v in result["summary"].items():
        d = f"  ({cmp['deltas'][k]:+.3f})" if cmp and k in cmp["deltas"] else ""
        print(f"  {k:22s} {v}{d}")
    failed = [c["id"] for c in result["cases"] if not c["passed"]]
    if failed:
        print("Failing cases:", ", ".join(failed))
    if cmp and (cmp["regressions"] or cmp["newly_failing"]):
        print("REGRESSION:", cmp["regressions"], "newly failing:", cmp["newly_failing"])
        return 1 if a.fail_on_regression else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
