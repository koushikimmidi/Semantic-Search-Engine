from backend.preprocessing.loader import DataLoader
from backend.preprocessing.cleaner import TextCleaner
from backend.preprocessing.tokenizer import Tokenizer


class PreprocessingPipeline:

    def __init__(self, file_path):
        self.loader = DataLoader(file_path)
        self.cleaner = TextCleaner()
        self.tokenizer = Tokenizer()

    def process(self):

        documents = self.loader.load_documents()

        processed = []

        for doc in documents:

            cleaned = self.cleaner.clean(doc["text"])

            tokens = self.tokenizer.tokenize(cleaned)

            processed.append({
                "id": doc["id"],
                "text": doc["text"],
                "tokens": tokens
            })

        return processed