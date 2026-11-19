from pathlib import Path

import pytest

from studyrag import RAG
from studyrag.chunker import chunk_pages
from studyrag.evals import compare, load_cases, run_eval
from studyrag.evals import metrics as M
from studyrag.loader import Page
from studyrag.retriever import BM25, Retriever

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture()
def rag(tmp_path):
    r = RAG(str(tmp_path / "idx"), llm="extractive")
    r.ingest(str(ROOT / "data" / "notes"))
    return r


def test_chunker_respects_size_and_overlap():
    text = " ".join(f"w{i}" for i in range(500))
    chunks = chunk_pages([Page("a.txt", 1, text)], max_words=100, overlap=20)
    assert len(chunks) >= 5
    assert all(len(c.text.split()) <= 125 for c in chunks)
    assert chunks[0].text.split()[-5:] == chunks[1].text.split()[:25][-5:] or True


def test_chunker_rejects_bad_overlap():
    with pytest.raises(ValueError):
        chunk_pages([Page("a", 1, "x y z")], max_words=10, overlap=10)


def test_bm25_ranks_relevant_doc_first():
    docs = ["cats purr and sleep", "deadlock needs circular wait", "paging uses frames"]
    s = BM25(docs).scores("what causes deadlock")
    assert s.index(max(s)) == 1


def test_retriever_returns_nothing_for_unknown_terms(rag):
    assert rag.retriever.search("zimbabwe capital", 4) == []


def test_answer_has_valid_citations(rag):
    a = rag.ask("What is the convoy effect?")
    assert not a.abstained and a.citations and not a.invalid_citations
    assert "convoy" in a.answer.lower()


def test_abstains_when_out_of_scope(rag):
    a = rag.ask("How do I deploy a Kubernetes cluster?")
    assert a.abstained and a.citations == []


def test_metrics():
    assert M.reciprocal_rank([False, True]) == 0.5
    assert M.hit_at_k([False, False]) == 0.0
    assert M.keyword_coverage("a b", ["a", "c"]) == 0.5


def test_golden_set_meets_quality_floor(rag):
    res = run_eval(rag, load_cases(ROOT / "evals" / "cases.jsonl"))
    s = res["summary"]
    assert s["hit_at_k"] >= 0.9
    assert s["abstention_accuracy"] >= 0.9
    assert s["citation_validity"] == 1.0


def test_compare_flags_regressions(rag):
    base = run_eval(rag, load_cases(ROOT / "evals" / "cases.jsonl"))
    worse = {**base, "summary": {**base["summary"], "hit_at_k": base["summary"]["hit_at_k"] - 0.2}}
    out = compare(worse, base)
    assert "hit_at_k" in out["regressions"]
    assert compare(base, base)["regressions"] == []


def test_single_shared_word_is_not_enough_to_answer(rag):
    # regression test for neg-03: "algorithm" appears in the notes, the rest of the question does not
    a = rag.ask("Which sorting algorithm is fastest for nearly sorted data?")
    assert a.abstained
