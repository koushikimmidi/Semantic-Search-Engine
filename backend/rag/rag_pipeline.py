from backend.llm import GemmaLLM


class RAGPipeline:

    def __init__(self):

        self.llm = GemmaLLM()

    def generate_answer(
        self,
        query,
        search_results,
        top_k=3
    ):

        context = "\n\n".join(

            result["text"]

            for result in search_results[:top_k]

        )

        answer = self.llm.generate(
            query,
            context
        )

        return {

            "query": query,

            "answer": answer,

            "sources": search_results[:top_k]

        }