class QueryExpander:
    """
    Expands abbreviations students commonly use in support emails
    and course questions.
    """

    def __init__(self):

        self.dictionary = {

            # Account & support
            "pwd": "password",
            "pw": "password",
            "pass": "password",
            "otp": "one time password",
            "acc": "account",
            "acct": "account",
            "login": "log in",
            "signin": "sign in",
            "2fa": "two factor authentication",

            # Payments
            "txn": "transaction",
            "trx": "transaction",
            "upi": "upi payment",
            "emi": "installment payment",
            "inv": "invoice",

            # Courses & certificates
            "cert": "certificate",
            "certs": "certificates",
            "faq": "frequently asked questions",
            "faqs": "frequently asked questions",
            "vid": "video",
            "vids": "videos",
            "lms": "learning platform",

            # Course topics
            "ai": "artificial intelligence",
            "ml": "machine learning",
            "dl": "deep learning",
            "nlp": "natural language processing",
            "dsa": "data structures algorithms",
            "ds": "data structures",
            "py": "python",
            "oop": "object oriented programming",
            "js": "javascript",
            "html": "html web development",
            "css": "css web development",
            "api": "application programming interface",
            "db": "database"
        }

    def expand(self, query):

        expanded = []

        for word in query.split():

            expanded.append(word)

            replacement = self.dictionary.get(word.lower())

            if replacement:
                expanded.append(replacement)

        return " ".join(expanded)
