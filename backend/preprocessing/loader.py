import json
from pathlib import Path


class DataLoader:
    def __init__(self, file_path):
        self.file_path = Path(file_path)

    def load_documents(self):
        with open(self.file_path, "r", encoding="utf-8") as file:
            documents = json.load(file)

        return documents