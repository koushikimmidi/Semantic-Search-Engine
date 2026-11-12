import os

from backend.loaders.txt_loader import TXTLoader
from backend.loaders.pdf_loader import PDFLoader
from backend.loaders.docx_loader import DOCXLoader
from backend.loaders.markdown_loader import MarkdownLoader


class DocumentLoader:

    def __init__(self):

        self.txt_loader = TXTLoader()
        self.pdf_loader = PDFLoader()
        self.docx_loader = DOCXLoader()
        self.markdown_loader = MarkdownLoader()

    def load(self, file_path):

        extension = os.path.splitext(file_path)[1].lower()

        if extension == ".txt":
            return self.txt_loader.load(file_path)

        elif extension == ".pdf":
            return self.pdf_loader.load(file_path)

        elif extension == ".docx":
            return self.docx_loader.load(file_path)

        elif extension == ".md":
            return self.markdown_loader.load(file_path)

        else:
            raise ValueError(f"Unsupported file type: {extension}")

    def load_pages(self, file_path):
        """
        Return [(page_number, text), ...].

        PDFs keep their real page numbers; other formats have no
        pages, so the whole document is page 1.
        """

        extension = os.path.splitext(file_path)[1].lower()

        if extension == ".pdf":
            return self.pdf_loader.load_pages(file_path)

        return [(1, self.load(file_path))]
