import os

from backend.loaders import DocumentLoader
from backend.chunking import TextChunker
from backend.metadata import MetadataBuilder
from backend.cache import HashCache


class DocumentIndexer:

    def __init__(self):

        self.loader = DocumentLoader()

        self.chunker = TextChunker(
            chunk_size=300,
            overlap=50
        )

        self.metadata = MetadataBuilder()

        self.cache = HashCache()

    def index_folder(self, folder_path):

        documents = []

        supported = (
            ".txt",
            ".pdf",
            ".docx",
            ".md"
        )

        for filename in os.listdir(folder_path):

            if not filename.lower().endswith(supported):
                continue

            file_path = os.path.join(
                folder_path,
                filename
            )

            # Skip files that have not changed
            if not self.cache.is_modified(file_path):

                print(f"Skipping {filename}")

                continue

            # Safely load the document
            try:

                text = self.loader.load(
                    file_path
                )

            except Exception as e:

                print(f"Skipping {filename}: {e}")

                continue

            chunks = self.chunker.chunk(
                text
            )

            metadata = self.metadata.build(
                chunks,
                source=filename,
                page=1
            )

            documents.extend(metadata)

        # Save updated hash cache
        self.cache.save()

        return documents