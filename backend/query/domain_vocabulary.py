class DomainVocabulary:
    """
    Maps support topics to the vocabulary of the knowledge-base
    section that covers them (policies, FAQs, technical support,
    course materials).
    """

    def __init__(self):

        self.terms = {

            # Policies
            "refund": ["refund policy", "eligibility"],
            "cancellation": ["cancellation policy"],
            "enrollment": ["enrollment policy"],
            "certificate": ["certificate policy", "completion"],

            # Technical support
            "password": ["password reset"],
            "login": ["login issues"],
            "playback": ["video playback"],
            "payment": ["payment troubleshooting"],

            # Course topics
            "python": ["programming"],
            "machine": ["machine learning"],
            "structures": ["data structures"],
            "web": ["web development"]
        }

    def expand(self, query):

        expanded = []

        seen = set(query.lower().split())

        for word in query.split():

            expanded.append(word)

            for term in self.terms.get(word.lower(), []):

                # Skip terms whose words are all already present.
                if set(term.split()) <= seen:
                    continue

                expanded.append(term)
                seen.update(term.split())

        return " ".join(expanded)
