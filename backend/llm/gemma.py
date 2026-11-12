import os

import ollama


FALLBACK_ANSWER = (
    "I cannot answer this based on the provided documents."
)


class GemmaLLM:

    def __init__(self):

        self.model = os.getenv(
            "OLLAMA_MODEL",
            "gemma4:latest"
        )

        # ----------------------------------------------------
        # Determine Ollama host
        #
        # Local Python:  localhost:11434
        # Docker:        host.docker.internal:11434
        # OLLAMA_HOST overrides both (docker-compose sets it).
        # ----------------------------------------------------

        configured_host = os.getenv("OLLAMA_HOST")

        if configured_host:
            self.host = configured_host
        elif os.path.exists("/.dockerenv"):
            self.host = "http://host.docker.internal:11434"
        else:
            self.host = "http://localhost:11434"

        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "220"))

        self.client = ollama.Client(
            host=self.host
        )

    # ========================================================
    # PROMPT
    # ========================================================

    def build_prompt(self, query, context):

        return f"""
You are a support assistant for an online academy.

Answer the question using ONLY the numbered sources below.
Be concise: 1-3 sentences.
After each sentence, cite the source number(s) it came from in
square brackets, for example [1] or [2][3].

If the sources do not contain enough information to answer, reply
exactly:
"{FALLBACK_ANSWER}"

Sources
-------

{context}

Question
--------

{query}

Answer
------
"""

    def _messages(self, query, context):

        return [
            {
                "role": "user",
                "content": self.build_prompt(query, context)
            }
        ]

    def _options(self):

        return {
            "num_predict": self.max_tokens,
            "temperature": 0.2
        }

    def _log_error(self, error):

        print("Ollama error:", str(error))
        print("Ollama host:", self.host)
        print("Ollama model:", self.model)

    # ========================================================
    # GENERATE
    # ========================================================

    def generate(
        self,
        query,
        context
    ):

        try:

            response = self.client.chat(
                model=self.model,
                messages=self._messages(query, context),
                options=self._options(),
                think=False
            )

            return response["message"]["content"].strip()

        except Exception as e:

            self._log_error(e)

            # Never return an error that looks like a valid answer;
            # the ConfidenceEngine treats this as unsupported.
            return FALLBACK_ANSWER

    def generate_stream(
        self,
        query,
        context
    ):
        """
        Yield the answer in pieces as the model produces them.
        On failure, yields the fallback answer instead (once, and
        only if nothing was produced yet).
        """

        produced = False

        try:

            stream = self.client.chat(
                model=self.model,
                messages=self._messages(query, context),
                options=self._options(),
                think=False,
                stream=True
            )

            for part in stream:

                text = part["message"]["content"]

                if text:
                    produced = True
                    yield text

        except Exception as e:

            self._log_error(e)

            if not produced:
                yield FALLBACK_ANSWER
