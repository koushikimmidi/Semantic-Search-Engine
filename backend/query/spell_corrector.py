from difflib import get_close_matches


class SpellCorrector:
    """
    Corrects misspelled query words against a vocabulary.

    The vocabulary starts with core support terms and is extended
    with every word that appears in the knowledge base
    (`update_vocabulary`), so corrections always point at words the
    documents actually contain. Words that are already known, short,
    or numeric are never changed.
    """

    BASE_VOCABULARY = [
        "refund", "cancellation", "cancel", "enrollment", "enroll",
        "certificate", "certification", "password", "reset", "login",
        "account", "payment", "transaction", "invoice", "billing",
        "course", "courses", "access", "video", "playback", "support",
        "technical", "student", "policy", "eligibility", "completion",
        "python", "machine", "learning", "structures", "development",
        "website", "browser", "email", "academy"
    ]

    def __init__(self, cutoff=0.8, min_length=4):

        self.cutoff = cutoff
        self.min_length = min_length
        self.vocabulary = set(self.BASE_VOCABULARY)

    def update_vocabulary(self, words):

        self.vocabulary = set(self.BASE_VOCABULARY)

        for word in words:

            word = str(word).lower()

            if len(word) >= self.min_length and word.isalpha():
                self.vocabulary.add(word)

    def correct_word(self, word):

        lower = word.lower()

        if (
            len(lower) < self.min_length
            or not lower.isalpha()
            or lower in self.vocabulary
        ):
            return word

        match = get_close_matches(
            lower,
            self.vocabulary,
            n=1,
            cutoff=self.cutoff
        )

        return match[0] if match else word

    def correct(self, query):

        return " ".join(
            self.correct_word(word)
            for word in query.split()
        )
