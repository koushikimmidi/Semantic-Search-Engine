class SynonymExpander:
    """
    Adds the wording used in the knowledge-base documents for the
    words students typically use.
    """

    def __init__(self):

        self.synonyms = {

            "refund": ["reimbursement"],
            "money": ["refund"],
            "reimbursement": ["refund"],

            "cancel": ["cancellation", "withdraw"],
            "withdraw": ["cancellation"],
            "unenroll": ["cancellation"],

            "login": ["sign", "account"],
            "signin": ["login"],
            "locked": ["login", "account"],

            "password": ["credentials"],
            "forgot": ["reset"],
            "forgotten": ["reset"],

            "pay": ["payment"],
            "paid": ["payment"],
            "charged": ["payment", "transaction"],
            "billing": ["payment", "invoice"],
            "deducted": ["payment", "transaction"],

            "certificate": ["certification"],
            "certification": ["certificate"],

            "video": ["playback", "lecture"],
            "lecture": ["video"],
            "buffering": ["playback", "video"],

            "enroll": ["enrollment", "registration"],
            "enrol": ["enrollment"],
            "register": ["enrollment"],
            "registration": ["enrollment"],

            "access": ["unlock"],
            "expire": ["expiry", "validity"],
            "expired": ["expiry", "validity"],

            "error": ["issue", "problem"],
            "bug": ["error", "issue"],
            "broken": ["issue", "problem"],

            "student": ["learner"]
        }

    def expand(self, query):

        expanded = []

        for word in query.split():

            expanded.append(word)

            expanded.extend(self.synonyms.get(word.lower(), []))

        return " ".join(expanded)
