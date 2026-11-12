from backend.chunking import TextChunker
from backend.chunking.text_chunker import clean_document_text
from backend.indexing import DocumentIndexer


PDF_LIKE_TEXT = """EDUSPHERE ACADEMY
Refund Policy
2. Refund Eligibility
Students may request a full refund within 7 calendar days from the date of course enrollment [cite: 47]. To be
eligible [cite: 47]:
The request must be submitted within 7 calendar days of enrollment [cite: 47].
Policy ID:
 EA-POL-001 [cite: 47]
•
EduSphere Academy — Refund Policy
Page 1 of 3
"""


def test_clean_removes_export_artefacts():

    cleaned = clean_document_text(PDF_LIKE_TEXT)

    assert "[cite" not in cleaned
    assert "Page 1 of 3" not in cleaned
    assert "\n•\n" not in cleaned
    assert "enrollment." in cleaned          # no space before the period
    assert "Policy ID: EA-POL-001" in cleaned  # label joined with value


def test_chunks_keep_whole_sentences_and_heading():

    chunks = TextChunker(chunk_size=700).chunk(PDF_LIKE_TEXT)

    eligibility = [c for c in chunks if "7 calendar days" in c]

    assert eligibility, chunks
    assert eligibility[0].startswith("2. Refund Eligibility:")
    # Wrapped lines are re-joined into one sentence.
    assert "To be eligible:" in eligibility[0]


def test_chunk_size_is_respected_with_sentence_overlap():

    text = "Section\n" + " ".join(
        f"Sentence number {i} talks about refunds and policies." for i in range(60)
    )

    chunker = TextChunker(chunk_size=200, overlap_sentences=1)
    chunks = chunker.chunk(text)

    assert len(chunks) > 5
    assert all(len(c) <= 200 for c in chunks)

    # The last sentence of one chunk starts the next one.
    first_last_sentence = chunks[0].split(": ", 1)[1].split(". ")[-1]
    assert first_last_sentence.rstrip(".") in chunks[1]


def test_very_long_sentence_is_split_on_words():

    text = "word " * 500

    chunks = TextChunker(chunk_size=100).chunk(text)

    assert all(len(c) <= 100 for c in chunks)
    assert sum(c.count("word") for c in chunks) >= 500


def test_empty_text_gives_no_chunks():

    assert TextChunker().chunk("") == []
    assert TextChunker().chunk("\n\n  \n") == []


def test_indexer_assigns_unique_ids_pages_and_chunk_numbers(knowledge_base):

    docs = DocumentIndexer().index_folder(str(knowledge_base))

    assert docs
    assert len({d["id"] for d in docs}) == len(docs)
    assert {d["source"] for d in docs} == {
        "password_reset.md",
        "policies/refund_policy.txt"
    }
    assert all(d["page"] == 1 and d["chunk"] >= 1 for d in docs)


def test_indexer_skips_unreadable_and_unsupported_files(tmp_path):

    (tmp_path / "notes.exe").write_bytes(b"MZ")
    (tmp_path / "broken.pdf").write_bytes(b"not a pdf")
    (tmp_path / "ok.txt").write_text("A valid sentence about refunds.", encoding="utf-8")

    docs = DocumentIndexer().index_folder(str(tmp_path))

    assert [d["source"] for d in docs] == ["ok.txt"]


def test_indexer_missing_folder_returns_empty(tmp_path):

    assert DocumentIndexer().index_folder(str(tmp_path / "missing")) == []
