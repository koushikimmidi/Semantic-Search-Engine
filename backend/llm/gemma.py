import ollama


class GemmaLLM:

    def __init__(self):

        self.model = "gemma4:latest"

    def generate(
        self,
        query,
        context
    ):

        prompt = f"""
You are an expert AI assistant.

Answer the question ONLY using the information in the context below.

If the context contains enough information,
explain the answer clearly in your own words.

Do NOT simply copy the context.

Context
-------

{context}

Question
--------

{query}

Answer
--------
"""

        response = ollama.chat(

            model=self.model,

            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response["message"]["content"]