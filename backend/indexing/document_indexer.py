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

        global_id = 0
        for root, dirs, files in os.walk(folder_path):

            for filename in files:

                if not filename.lower().endswith(supported):
                    continue

                file_path = os.path.join(
                    root,
                    filename
                )

                # Get relative path for metadata source (e.g. subfolder/file.txt)
                rel_source = os.path.relpath(file_path, folder_path).replace("\\", "/")

                # -------------------------------------------------
                # TEMPORARILY DISABLE HASH CACHE
                # Always load every file
                # -------------------------------------------------
                print(f"Loading {rel_source}")

                # Safely load the document
                try:

                    text = self.loader.load(
                        file_path
                    )

                except Exception as e:

                    print(f"Skipping {rel_source}: {e}")

                    continue

                chunks = self.chunker.chunk(
                    text
                )

                metadata = self.metadata.build(
                    chunks,
                    source=rel_source,
                    page=1
                )

                for doc in metadata:
                    doc["id"] = global_id
                    global_id += 1

                documents.extend(metadata)

        # Cache disabled for now
        # self.cache.save()

        return documents