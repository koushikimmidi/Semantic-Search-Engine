from difflib import get_close_matches


class SpellCorrector:

    def __init__(self):

        self.vocabulary = [

            "artificial",
            "intelligence",
            "machine",
            "learning",
            "deep",
            "python",
            "database",
            "retrieval",
            "generation",
            "language",
            "model",
            "network",
            "neural",
            "computer",
            "vision",
            "fastapi",
            "bm25",
            "semantic",
            "search",
            "engine"
        ]

    def correct(self, query):

        corrected = []

        for word in query.split():

            match = get_close_matches(
                word.lower(),
                self.vocabulary,
                n=1,
                cutoff=0.75
            )

            if match:

                corrected.append(match[0])

            else:

                corrected.append(word)

        return " ".join(corrected)