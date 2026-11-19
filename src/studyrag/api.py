"""Minimal web API + page. Needs `pip install studyrag[api]`."""
from .rag import RAG

PAGE = """<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>StudyRAG</title>
<style>
:root{--bg:#fff;--fg:#1a1a1a;--mut:#666;--card:#f4f4f5}
@media(prefers-color-scheme:dark){:root{--bg:#151515;--fg:#eee;--mut:#9a9a9a;--card:#222}}
body{font:16px/1.5 system-ui,sans-serif;background:var(--bg);color:var(--fg);max-width:720px;margin:2rem auto;padding:0 1rem}
input{width:100%;padding:10px;font-size:16px;border-radius:8px;border:1px solid var(--mut);background:var(--card);color:var(--fg);box-sizing:border-box}
.a{background:var(--card);border-radius:8px;padding:12px;margin-top:12px;white-space:pre-wrap}.c{color:var(--mut);font-size:13px;margin-top:6px}
</style>
<h1>StudyRAG</h1><p>Ask a question about your notes.</p>
<input id="q" placeholder="e.g. What is the convoy effect?" autofocus>
<div id="out"></div>
<script>
const q=document.getElementById('q'),out=document.getElementById('out');
q.addEventListener('keydown',async e=>{if(e.key!=='Enter'||!q.value.trim())return;
out.textContent='Thinking...';
const r=await fetch('/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:q.value})});
const d=await r.json();out.innerHTML='';const a=document.createElement('div');a.className='a';a.textContent=d.answer;out.appendChild(a);
d.citations.forEach(c=>{const s=document.createElement('div');s.className='c';s.textContent='['+c.n+'] '+c.source+' p.'+c.page+' - '+c.snippet;out.appendChild(s)});});
</script>"""


def create_app(rag: RAG):
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse
    from pydantic import BaseModel

    class Q(BaseModel):
        question: str

    app = FastAPI(title="StudyRAG")
    rag.load()

    @app.get("/", response_class=HTMLResponse)
    def home():
        return PAGE

    @app.get("/health")
    def health():
        return {"status": "ok", "chunks": len(rag.chunks), "mode": rag.mode}

    @app.post("/ask")
    def ask(q: Q):
        return rag.ask(q.question).to_dict()

    return app


def serve(rag: RAG, port: int = 8000) -> None:
    import uvicorn

    uvicorn.run(create_app(rag), host="0.0.0.0", port=port)
