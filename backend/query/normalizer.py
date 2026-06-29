import re


class QueryNormalizer:

    def normalize(self, query):

        # Convert to lowercase
        query = query.lower()

        # Remove punctuation
        query = re.sub(r"[^\w\s]", "", query)

        # Remove extra spaces
        query = " ".join(query.split())

        return query