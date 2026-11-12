import json

import pytest

from backend.query.pipeline import QueryPipeline
from backend.query.spell_corrector import SpellCorrector
from backend.intent.intent_classifier import IntentClassifier
from backend.intent.intent_detector import IntentDetector

from tests.conftest import HashingEncoder


# ============================================================
# QUERY PIPELINE
# ============================================================

def test_query_pipeline_expands_education_terms():

    stages = QueryPipeline().process("I forgot my pwd, pls help!")

    final = stages["Domain Expanded"]

    assert "password" in final
    assert "reset" in final        # forgot -> reset synonym
    assert "i" not in final.split()


def test_stopword_removal_never_returns_empty():

    stages = QueryPipeline().process("what is the")

    assert stages["Stop Words Removed"].strip()


def test_negations_are_kept():

    stages = QueryPipeline().process("video is not playing")

    assert "not" in stages["Stop Words Removed"].split()


def test_spell_corrector_uses_corpus_vocabulary():

    corrector = SpellCorrector()
    corrector.update_vocabulary(["refund", "certificate", "enrollment"])

    assert corrector.correct("refnd certifcate") == "refund certificate"
    # Known, short and numeric words are left alone.
    assert corrector.correct("refund at 2026") == "refund at 2026"


# ============================================================
# INTENT
# ============================================================

@pytest.fixture
def classifier(tmp_path):

    examples = {
        "PASSWORD_RESET": ["forgot my password", "reset my password", "password reset link"],
        "REFUND": ["refund my money", "want a refund", "refund period"],
        "OUT_OF_SCOPE": ["capital of japan", "weather today", "tell a joke"]
    }

    path = tmp_path / "examples.json"
    path.write_text(json.dumps(examples), encoding="utf-8")

    return IntentClassifier(
        encoder=HashingEncoder(),
        examples_path=str(path),
        min_similarity=0.2
    )


def test_classifier_predicts_known_intent(classifier):

    result = classifier.predict("I forgot the password")

    assert result["intent"] == "PASSWORD_RESET"
    assert 0.5 <= result["confidence"] <= 1.0


def test_classifier_maps_out_of_scope_to_unknown(classifier):

    assert classifier.predict("what is the capital of japan")["intent"] == "UNKNOWN"
    assert classifier.predict("zzz qqq")["intent"] == "UNKNOWN"
    assert classifier.predict("   ")["intent"] == "UNKNOWN"


def test_rules_detect_specific_phrases():

    detector = IntentDetector(use_classifier=False)

    assert detector.detect("How do I reset my password?")["intent"] == "PASSWORD_RESET"
    assert detector.detect("The video is not playing")["intent"] == "TECHNICAL_SUPPORT"
    assert detector.detect("hello there")["intent"] == "UNKNOWN"


def test_hybrid_uses_classifier_when_rules_find_nothing(classifier):

    detector = IntentDetector(classifier=classifier, use_classifier=True)

    result = detector.detect("password link never arrived")

    assert result["intent"] == "PASSWORD_RESET"
    assert result["method"] == "classifier"


def test_hybrid_agreement_boosts_confidence(classifier):

    detector = IntentDetector(classifier=classifier, use_classifier=True)

    result = detector.detect("please reset my password")

    assert result["intent"] == "PASSWORD_RESET"
    assert result["method"] == "rules+classifier"
    assert result["confidence"] >= 0.9


def test_hybrid_falls_back_to_rules_when_classifier_fails():

    class Broken:
        def predict(self, query):
            raise RuntimeError("model missing")

    detector = IntentDetector(classifier=Broken(), use_classifier=True)

    assert detector.detect("I want a refund")["intent"] == "REFUND"
