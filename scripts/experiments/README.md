# Experiments

Stand-alone scripts written while the engine was being built, one per component
(BM25, dense search, hybrid fusion, reranking, chunking, caching, the RAG pipeline…).
They are kept as a record of how each piece was developed and as quick manual checks.

They are **not** part of the application or the automated test suite (that lives in
[`tests/`](../../tests)). Run any of them from the project root, for example:

```bash
python -m scripts.experiments.test_hybrid
python -m scripts.experiments.compare_all
```

Some scripts target the original sample dataset (`data/raw/sample_documents.json`)
rather than the current knowledge base.
