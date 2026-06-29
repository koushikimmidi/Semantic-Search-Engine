class QueryExpander:

    def __init__(self):

        self.dictionary = {

            "ai": "Artificial Intelligence",

            "ml": "Machine Learning",

            "nlp": "Natural Language Processing",

            "cv": "Computer Vision",

            "llm": "Large Language Model",

            "rag": "Retrieval Augmented Generation",

            "api": "Application Programming Interface",

            "db": "Database",

            "dl": "Deep Learning",

            "nn": "Neural Network"
        }

    def expand(self, query):

        words = query.split()

        expanded = []

        for word in words:

            expanded.append(word)

            key = word.lower()

            if key in self.dictionary:

                expanded.append(
                    self.dictionary[key]
                )

        return " ".join(expanded)