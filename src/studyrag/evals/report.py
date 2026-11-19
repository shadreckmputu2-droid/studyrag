"""Self-contained HTML report."""
import html


def render(result: dict, cmp: dict | None = None) -> str:
    s, deltas = result["summary"], (cmp or {}).get("deltas", {})
    pct = {"hit_at_k", "mrr", "keyword_coverage", "citation_validity", "abstention_accuracy", "faithfulness"}
    cards = ""
    for k, v in s.items():
        if k == "n_cases":
            continue
        val = f"{v * 100:.1f}%" if k in pct else f"{v:.1f} ms"
        d = deltas.get(k)
        badge = ""
        if d is not None:
            cls = "up" if d > 0 else "down" if d < 0 else "flat"
            badge = f'<span class="d {cls}">{d * 100:+.1f} pts</span>'
        cards += f'<div class="card"><div class="l">{html.escape(k)}</div><div class="v">{val}</div>{badge}</div>'
    rows = ""
    for c in result["cases"]:
        rows += (
            f'<tr class="{"ok" if c["passed"] else "bad"}"><td>{html.escape(c["id"])}</td>'
            f'<td>{html.escape(c["question"])}</td><td>{html.escape(c["answer"][:220])}</td>'
            f'<td>{"pass" if c["passed"] else "FAIL"}</td></tr>'
        )
    m = result["meta"]
    reg = ""
    if cmp and cmp["regressions"]:
        reg = f'<p class="alert">Regressions: {", ".join(cmp["regressions"])}</p>'
    return f"""<!doctype html><meta charset="utf-8"><title>StudyRAG eval</title>
<style>
:root{{--bg:#fff;--fg:#1a1a1a;--mut:#666;--card:#f4f4f5;--bd:#ddd;--ok:#14803c;--bad:#b42318}}
@media(prefers-color-scheme:dark){{:root{{--bg:#151515;--fg:#eee;--mut:#9a9a9a;--card:#222;--bd:#333;--ok:#4ade80;--bad:#f87171}}}}
body{{font:15px/1.5 system-ui,sans-serif;background:var(--bg);color:var(--fg);margin:2rem auto;max-width:980px;padding:0 1rem}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}}
.card{{background:var(--card);border-radius:8px;padding:12px}}.l{{color:var(--mut);font-size:12px}}.v{{font-size:22px;font-weight:600}}
.d{{font-size:12px}}.up{{color:var(--ok)}}.down{{color:var(--bad)}}.flat{{color:var(--mut)}}
table{{width:100%;border-collapse:collapse;margin-top:1.5rem;font-size:13px}}td,th{{border-bottom:1px solid var(--bd);padding:6px;text-align:left;vertical-align:top}}
tr.bad td:last-child{{color:var(--bad);font-weight:600}}tr.ok td:last-child{{color:var(--ok)}}.alert{{color:var(--bad);font-weight:600}}
</style>
<h1>StudyRAG evaluation</h1>
<p style="color:var(--mut)">{m["timestamp"]} &middot; retrieval: {m["mode"]} &middot; k={m["k"]} &middot; generator: {html.escape(str(m["llm"]))} &middot; {s["n_cases"]} cases &middot; {m["chunks"]} chunks</p>
{reg}<div class="grid">{cards}</div>
<table><tr><th>ID</th><th>Question</th><th>Answer</th><th>Result</th></tr>{rows}</table>"""
