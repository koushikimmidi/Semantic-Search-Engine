from backend.llm import GemmaLLM
from backend.confidence.confidence_engine import ConfidenceEngine
from backend.automation.message_router import MessageRouter
from backend.intent.intent_detector import IntentDetector


class RAGPipeline:

    def __init__(self):

        self.llm = GemmaLLM()

        self.confidence_engine = ConfidenceEngine()

        self.message_router = MessageRouter()

        self.intent_detector = IntentDetector()

    def generate_answer(
        self,
        query,
        search_results,
        top_k=3
    ):

        # ----------------------------------------------------
        # Detect user intent
        # ----------------------------------------------------

        intent = self.intent_detector.detect(
            query
        )

        # ----------------------------------------------------
        # Select top search results
        # ----------------------------------------------------

        selected_results = search_results[:top_k]

        # ----------------------------------------------------
        # Build context for the LLM
        # ----------------------------------------------------

        context = "\n\n".join(

            result["text"]

            for result in selected_results

        )

        # ----------------------------------------------------
        # Generate grounded answer
        # ----------------------------------------------------

        # No evidence: skip the LLM call entirely.
        if not selected_results:

            answer = (
                "I cannot answer this based on the provided "
                "documents."
            )

        else:

            answer = self.llm.generate(
                query,
                context
            )

        # ----------------------------------------------------
        # Evaluate confidence
        #
        # Intent information is passed to the confidence
        # engine so retrieved evidence must also match the
        # detected intent before automatic reply.
        # ----------------------------------------------------

        confidence = self.confidence_engine.evaluate(
            answer,
            selected_results,
            intent
        )

        # ----------------------------------------------------
        # Determine routing decision
        # ----------------------------------------------------

        routing = self.message_router.route(
            confidence
        )

        # ----------------------------------------------------
        # Return complete RAG response
        # ----------------------------------------------------

        return {

            "query": query,

            "intent": intent,

            "answer": answer,

            "sources": selected_results,

            "confidence": confidence,

            "routing": routing

        }