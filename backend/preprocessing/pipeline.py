from backend.indexing import DocumentIndexer
from backend.preprocessing.cleaner import TextCleaner
from backend.preprocessing.tokenizer import Tokenizer


class PreprocessingPipeline:

    def __init__(self, folder_path):

        self.folder_path = folder_path

        self.indexer = DocumentIndexer()

        self.cleaner = TextCleaner()

        self.tokenizer = Tokenizer()

    def process(self):

        # Load all documents from the folder
        documents = self.indexer.index_folder(
            self.folder_path
        )

        processed = []

        for doc in documents:

            cleaned = self.cleaner.clean(
                doc["text"]
            )

            tokens = self.tokenizer.tokenize(
                cleaned
            )

            processed.append({

                "id": doc["id"],

                "text": doc["text"],

                "tokens": tokens,

                "source": doc.get("source"),

                "page": doc.get("page")

            })

        return processed