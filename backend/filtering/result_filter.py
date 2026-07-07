class ResultFilter:

    def filter(

        self,

        documents,

        source=None,

        extension=None,

        page=None

    ):

        results = []

        for document in documents:

            if source is not None:

                if document["source"] != source:

                    continue

            if extension is not None:

                if not document["source"].lower().endswith(

                    extension.lower()

                ):

                    continue

            if page is not None:

                if document["page"] != page:

                    continue

            results.append(document)

        return results