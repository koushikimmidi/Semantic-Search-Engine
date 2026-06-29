from docx import Document


class DOCXLoader:

    def load(self, file_path):

        document = Document(file_path)

        text = ""

        for paragraph in document.paragraphs:
            text += paragraph.text + "\n"

        return text