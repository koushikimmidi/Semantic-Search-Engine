import markdown
from bs4 import BeautifulSoup


class MarkdownLoader:

    def load(self, file_path):

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as file:

            html = markdown.markdown(
                file.read()
            )

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        return soup.get_text()