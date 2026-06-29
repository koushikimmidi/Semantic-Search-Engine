import faiss


class IndexStorage:

    @staticmethod
    def save(index, path):

        faiss.write_index(
            index,
            path
        )

    @staticmethod
    def load(path):

        return faiss.read_index(
            path
        )