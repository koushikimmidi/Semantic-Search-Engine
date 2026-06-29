class SynonymExpander:

    def __init__(self):

        self.synonyms = {

            "car": [
                "automobile",
                "vehicle"
            ],

            "student": [
                "learner",
                "pupil"
            ],

            "code": [
                "program",
                "software"
            ],

            "database": [
                "db"
            ],

            "bug": [
                "error",
                "issue"
            ],

            "ai": [
                "artificial intelligence",
                "machine intelligence"
            ],

            "python": [
                "programming language"
            ]
        }

    def expand(self, query):

        words = query.split()

        expanded = []

        for word in words:

            expanded.append(word)

            key = word.lower()

            if key in self.synonyms:

                expanded.extend(
                    self.synonyms[key]
                )

        return " ".join(expanded)