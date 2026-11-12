class StopWordRemover:
    """
    Removes filler words before keyword matching.

    Negations ("not", "no", "cannot", "cant") are deliberately kept:
    "video not playing" means something different from "video playing".
    """

    def __init__(self):

        self.stop_words = {
            "a", "an", "the", "is", "are", "was", "were", "be", "been",
            "am", "about", "tell", "me", "please", "of", "for", "to",
            "on", "in", "at", "by", "and", "or", "with", "what", "how",
            "explain", "i", "im", "ive", "my", "mine", "we", "our",
            "you", "your", "it", "its", "this", "that", "these",
            "those", "do", "does", "did", "can", "could", "would",
            "should", "will", "shall", "may", "might", "hi", "hello",
            "hey", "dear", "thanks", "thank", "regards", "kindly",
            "there", "any", "some", "which", "when", "where", "who",
            "why", "so", "if", "then", "also", "just", "know", "want",
            "need", "help", "from"
        }

    def remove(self, query):

        filtered = [
            word
            for word in query.split()
            if word not in self.stop_words
        ]

        # Never return an empty query; fall back to the input.
        return " ".join(filtered) if filtered else query
