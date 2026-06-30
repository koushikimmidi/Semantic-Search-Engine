import os
import faiss


class FAISSIndexer:

    def __init__(self, dimension):

        self.dimension = dimension

        self.index = faiss.IndexFlatL2(
            dimension
        )

    def build(self, embeddings):

        self.index.add(
            embeddings
        )

    def save(

        self,

        path="data/index/faiss.index"

    ):

        os.makedirs(
            "data/index",
            exist_ok=True
        )

        faiss.write_index(
            self.index,
            path
        )

    def load(

        self,

        path="data/index/faiss.index"

    ):

        self.index = faiss.read_index(
            path
        )

    def exists(

        self,

        path="data/index/faiss.index"

    ):

        return os.path.exists(path)