"""
Intent detection accuracy on the labelled evaluation set.

Compares rules only, classifier only, and the hybrid detector.

    python -m scripts.evaluate_intent
"""

import json
import sys
from collections import Counter

from backend.intent.intent_detector import IntentDetector


EVAL_PATH = "data/eval/eval_set.json"


def accuracy(predicted, expected):

    correct = sum(1 for p, e in zip(predicted, expected) if p == e)

    return correct / len(expected) if expected else 0.0


def main(path=EVAL_PATH):

    with open(path, "r", encoding="utf-8") as file:
        items = json.load(file)

    detector = IntentDetector(use_classifier=True)

    expected = [item["intent"] for item in items]

    rules = [detector.detect_rules(item["query"])["intent"] for item in items]
    model = [detector.detect_classifier(item["query"])["intent"] for item in items]
    hybrid = [detector.detect(item["query"])["intent"] for item in items]

    print("=" * 70)
    print(f"INTENT ACCURACY ({len(items)} labelled queries)")
    print("=" * 70)
    print(f"Rules only      : {accuracy(rules, expected):.1%}")
    print(f"Classifier only : {accuracy(model, expected):.1%}")
    print(f"Hybrid          : {accuracy(hybrid, expected):.1%}")

    errors = [
        (item["query"], item["intent"], h)
        for item, h in zip(items, hybrid)
        if h != item["intent"]
    ]

    if errors:
        print("\nHybrid mistakes:")
        for query, want, got in errors:
            print(f"  - {query[:55]:<55} expected {want:<18} got {got}")

    confusions = Counter((e, h) for e, h in zip(expected, hybrid) if e != h)

    if confusions:
        print("\nMost common confusions:", confusions.most_common(5))

    return accuracy(hybrid, expected)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else EVAL_PATH)
