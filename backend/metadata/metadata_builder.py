class MetadataBuilder:

    def build(

        self,

        chunks,

        source,

        page=1

    ):

        documents = []

        for index, chunk in enumerate(chunks, start=1):

            documents.append(

                {

                    "id": index,

                    "text": chunk,

                    "source": source,

                    "page": page,

                    "chunk": index

                }

            )

        return documents