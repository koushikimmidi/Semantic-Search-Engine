class TXTLoader:

    def load(self, file_path):

        # errors="replace" keeps one badly encoded file from
        # stopping the whole knowledge base from loading.
        with open(
            file_path,
            "r",
            encoding="utf-8",
            errors="replace"
        ) as file:

            return file.read()
