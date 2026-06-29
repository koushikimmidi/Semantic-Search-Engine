import faiss
import os
import pickle


class IndexPersistence:

    def __init__(self):

        self.index_file = "data/index/faiss.index"

        self.metadata_file = "data/index/documents.pkl"

    def save(self, index, documents):

        os.makedirs(
            "data/index",
            exist_ok=True
        )

        faiss.write_index(
            index,
            self.index_file
        )

        with open(
            self.metadata_file,
            "wb"
        ) as file:

            pickle.dump(
                documents,
                file
            )

    def exists(self):

        return (
            os.path.exists(self.index_file)
            and
            os.path.exists(self.metadata_file)
        )

    def load(self):

        index = faiss.read_index(
            self.index_file
        )

        with open(
            self.metadata_file,
            "rb"
        ) as file:

            documents = pickle.load(file)

        return index, documents