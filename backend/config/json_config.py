import json


class JsonConfig:

    def __init__(self, file_path):

        with open(file_path, "r") as file:

            self.config = json.load(file)

    @property
    def project_name(self):
        return self.config["project_name"]

    @property
    def version(self):
        return self.config["version"]

    @property
    def dataset_path(self):
        return self.config["dataset"]["path"]

    @property
    def embedding_model(self):
        return self.config["embedding"]["model"]

    @property
    def top_k(self):
        return self.config["search"]["top_k"]

    @property
    def faiss_index(self):
        return self.config["faiss"]["index_path"]