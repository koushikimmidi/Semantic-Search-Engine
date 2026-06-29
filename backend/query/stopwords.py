class StopWordRemover:

    def __init__(self):

        self.stop_words = {

            "a",
            "an",
            "the",
            "is",
            "are",
            "was",
            "were",
            "about",
            "tell",
            "me",
            "please",
            "of",
            "for",
            "to",
            "on",
            "in",
            "and",
            "or",
            "with",
            "what",
            "how",
            "explain"
        }

    def remove(self, query):

        words = query.split()

        filtered = [

            word

            for word in words

            if word not in self.stop_words

        ]

        return " ".join(filtered)