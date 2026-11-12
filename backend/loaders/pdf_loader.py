import fitz


class PDFLoader:

    def load_pages(self, file_path):
        """
        Return [(page_number, text), ...] with 1-based page numbers.
        """

        pages = []

        with fitz.open(file_path) as document:

            for number, page in enumerate(document, start=1):
                pages.append((number, page.get_text()))

        return pages

    def load(self, file_path):

        return "\n".join(
            text for _, text in self.load_pages(file_path)
        )
