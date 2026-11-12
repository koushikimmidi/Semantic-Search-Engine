import os
import ollama


class GemmaLLM:

    def __init__(self):

        self.model = os.getenv(
            "OLLAMA_MODEL",
            "gemma4:latest"
        )

        # ----------------------------------------------------
        # Determine Ollama host
        #
        # Local Python:
        #     localhost:11434
        #
        # Docker:
        #     host.docker.internal:11434
        #
        # An environment variable can override both.
        # ----------------------------------------------------

        configured_host = os.getenv(
            "OLLAMA_HOST"
        )

        if configured_host:

            self.host = configured_host

        elif os.path.exists("/.dockerenv"):

            self.host = (
                "http://host.docker.internal:11434"
            )

        else:

            self.host = (
                "http://localhost:11434"
            )

        self.client = ollama.Client(
            host=self.host
        )

    def generate(
        self,
        query,
        context
    ):

        prompt = f"""
You are an expert AI assistant.

Answer the question ONLY using the information in the context below.
Be extremely concise. Limit your answer to 1-3 sentences.

If the context does not contain enough information to answer, state exactly:
"I cannot answer this based on the provided documents."

Context
-------

{context}

Question
--------

{query}

Answer
--------
"""

        try:

            response = self.client.chat(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                options={
                    "num_predict": 128,
                    "temperature": 0.2
                },
                think=False
            )

            return response["message"]["content"]

        except Exception as e:

            print(
                "Ollama error:",
                str(e)
            )

            print(
                "Ollama host:",
                self.host
            )

            print(
                "Ollama model:",
                self.model
            )

            # ------------------------------------------------
            # IMPORTANT
            #
            # Do not return an error message that looks like
            # a valid AI answer. The ConfidenceEngine must
            # treat infrastructure failure as unsupported.
            # ------------------------------------------------

            return (
                "I cannot answer this based on the provided "
                "documents."
            )