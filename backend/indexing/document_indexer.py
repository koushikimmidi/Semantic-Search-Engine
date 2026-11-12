import os

from backend.loaders import DocumentLoader
from backend.chunking import TextChunker


SUPPORTED_EXTENSIONS = (
    ".txt",
    ".pdf",
    ".docx",
    ".md"
)


class DocumentIndexer:
    """
    Walks a folder, loads every supported document page by page,
    and splits it into sentence-aware chunks with metadata:

        {"id", "text", "source", "page", "chunk"}

    `id` is unique across the whole folder; `chunk` is the chunk
    number inside its file (1-based).
    """

    def __init__(self, chunk_size=None):

        self.loader = DocumentLoader()

        self.chunker = TextChunker(
            chunk_size=chunk_size or int(
                os.getenv("CHUNK_SIZE", "700")
            )
        )

    def index_folder(self, folder_path):

        documents = []

        if not os.path.isdir(folder_path):
            return documents

        global_id = 0

        for root, dirs, files in os.walk(folder_path):

            # Deterministic order -> stable ids between restarts.
            dirs.sort()

            for filename in sorted(files):

                if not filename.lower().endswith(SUPPORTED_EXTENSIONS):
                    continue

                file_path = os.path.join(root, filename)

                rel_source = os.path.relpath(
                    file_path,
                    folder_path
                ).replace("\\", "/")

                try:

                    pages = self.loader.load_pages(file_path)

                except Exception as e:

                    print(f"Skipping {rel_source}: {e}")

                    continue

                chunk_number = 0

                for page_number, page_text in pages:

                    for chunk_text in self.chunker.chunk(page_text):

                        chunk_number += 1

                        documents.append({
                            "id": global_id,
                            "text": chunk_text,
                            "source": rel_source,
                            "page": page_number,
                            "chunk": chunk_number
                        })

                        global_id += 1

                print(f"Loaded {rel_source} ({chunk_number} chunks)")

        return documents
