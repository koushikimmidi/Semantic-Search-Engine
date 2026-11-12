"""
End-to-end evaluation on data/eval/eval_set.json.

Retrieval mode (fast, no LLM):
    python -m scripts.evaluate_pipeline
    Shows cross-encoder scores for answerable vs. unanswerable
    questions and suggests confidence thresholds.

Full mode (runs Gemma for every question, slow):
    python -m scripts.evaluate_pipeline --full
    Reports auto-reply precision (share of auto replies that were
    answerable questions), coverage, and intent accuracy.
"""

import json
import sys
import time

from dotenv import load_dotenv

load_dotenv()

from backend.engine.search_engine import SearchEngine  # noqa: E402


EVAL_PATH = "data/eval/eval_set.json"
KB_PATH = "data/documents/education"


def load_items():

    with open(EVAL_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def retrieval_report(engine, items):

    rows = []

    for item in items:

        results = engine.search(item["query"])
        top = results[0]["cross_score"] if results else float("-inf")
        second = results[1]["cross_score"] if len(results) > 1 else top

        rows.append((item, top, top - second, results[0]["source"] if results else "-"))

    print("\n" + "=" * 90)
    print("CROSS-ENCODER TOP SCORE (original query)")
    print("=" * 90)

    for item, top, gap, source in sorted(rows, key=lambda r: -r[1]):

        flag = "answerable  " if item["answerable"] else "UNANSWERABLE"

        print(f"{top:7.2f}  gap {gap:5.2f}  {flag}  {item['query'][:48]:<48} {source}")

    answerable = sorted(r[1] for r in rows if r[0]["answerable"])
    unanswerable = sorted(r[1] for r in rows if not r[0]["answerable"])

    print("\nAnswerable   scores: min %.2f  median %.2f" % (
        answerable[0], answerable[len(answerable) // 2]))
    print("Unanswerable scores: max %.2f  median %.2f" % (
        unanswerable[-1], unanswerable[len(unanswerable) // 2]))

    return rows


def full_report(engine, items):

    from backend.rag import RAGPipeline

    rag = RAGPipeline()

    auto = auto_correct = 0
    answerable_total = sum(1 for item in items if item["answerable"])
    intent_correct = 0

    print("\n" + "=" * 90)
    print("FULL PIPELINE")
    print("=" * 90)

    for item in items:

        start = time.time()
        results = engine.search(item["query"])
        response = rag.generate_answer(item["query"], results)

        route = response["routing"]["route"]
        intent = response["intent"]["intent"]

        if intent == item["intent"]:
            intent_correct += 1

        if route == "AUTO_REPLY":
            auto += 1
            if item["answerable"]:
                auto_correct += 1

        verdict = (
            "ok" if (route == "AUTO_REPLY") == item["answerable"]
            else ("MISSED" if item["answerable"] else "WRONG-AUTO")
        )

        print(
            f"{verdict:<10} {route:<12} {intent:<18} "
            f"{time.time() - start:4.1f}s  {item['query'][:45]}"
        )

    precision = auto_correct / auto if auto else 1.0
    coverage = auto_correct / answerable_total if answerable_total else 0.0

    print("\nAuto replies           :", auto)
    print(f"Auto-reply precision   : {precision:.1%}  (auto replies that were answerable)")
    print(f"Auto-reply coverage    : {coverage:.1%}  (answerable questions auto-replied)")
    print(f"Intent accuracy        : {intent_correct / len(items):.1%}")


def main():

    items = load_items()

    engine = SearchEngine(KB_PATH)
    engine.load()

    if "--full" in sys.argv:
        full_report(engine, items)
    else:
        retrieval_report(engine, items)


if __name__ == "__main__":
    main()
