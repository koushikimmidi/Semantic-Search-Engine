class DomainVocabulary:

    def __init__(self):

        self.terms = {

            "ai": [
                "artificial intelligence",
                "machine intelligence",
                "intelligent systems"
            ],

            "ml": [
                "machine learning",
                "supervised learning",
                "unsupervised learning"
            ],

            "dl": [
                "deep learning",
                "neural network"
            ],

            "nlp": [
                "natural language processing",
                "text mining",
                "language model"
            ],

            "cv": [
                "computer vision",
                "image processing",
                "object detection"
            ],

            "llm": [
                "large language model",
                "gpt",
                "bert",
                "transformer"
            ],

            "rag": [
                "retrieval augmented generation",
                "vector database",
                "semantic search"
            ],

            "transformer": [
                "attention",
                "encoder",
                "decoder",
                "bert",
                "gpt"
            ],

            "faiss": [
                "vector search",
                "similarity search"
            ],

            "bm25": [
                "information retrieval",
                "ranking algorithm"
            ],

            "python": [
                "programming language",
                "object oriented programming"
            ]
        }

    def expand(self, query):

        words = query.split()

        expanded = []

        for word in words:

            expanded.append(word)

            key = word.lower()

            if key in self.terms:

                expanded.extend(
                    self.terms[key]
                )

        return " ".join(expanded)