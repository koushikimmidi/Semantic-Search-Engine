import hashlib
import os
import pickle
import threading

import numpy as np


class ChunkEmbeddingCache:
    """
    Persistent cache of chunk embeddings keyed by
    sha256(model name + chunk text).

    When the knowledge base changes, only new or edited chunks are
    encoded; everything else is read from disk. Entries for chunks
    that no longer exist are pruned on save.
    """

    def __init__(
        self,
        model_name,
        cache_file="data/index/embedding_cache.pkl"
    ):

        self.model_name = model_name
        self.cache_file = cache_file
        self._lock = threading.Lock()
        self._vectors = self._load()

    # ========================================================
    # KEYS
    # ========================================================

    def key(self, text):

        return hashlib.sha256(
            (self.model_name + "\x00" + text).encode("utf-8")
        ).hexdigest()

    # ========================================================
    # PERSISTENCE
    # ========================================================

    def _load(self):

        if not os.path.exists(self.cache_file):
            return {}

        try:

            with open(self.cache_file, "rb") as file:
                data = pickle.load(file)

            if (
                isinstance(data, dict)
                and data.get("model") == self.model_name
                and isinstance(data.get("vectors"), dict)
            ):
                return data["vectors"]

        except Exception as e:

            print("Embedding cache unreadable, rebuilding:", str(e))

        return {}

    def _save(self, keep_keys):

        directory = os.path.dirname(self.cache_file)

        if directory:
            os.makedirs(directory, exist_ok=True)

        self._vectors = {
            key: vector
            for key, vector in self._vectors.items()
            if key in keep_keys
        }

        temp_file = self.cache_file + ".tmp"

        with open(temp_file, "wb") as file:
            pickle.dump(
                {"model": self.model_name, "vectors": self._vectors},
                file,
                protocol=pickle.HIGHEST_PROTOCOL
            )

        os.replace(temp_file, self.cache_file)

    # ========================================================
    # ENCODE WITH CACHE
    # ========================================================

    def encode(self, texts, encode_function):
        """
        Return a float32 matrix of embeddings for `texts`,
        calling `encode_function(list_of_texts)` only for texts
        that are not cached.
        """

        with self._lock:

            keys = [self.key(text) for text in texts]

            missing_positions = [
                position
                for position, key in enumerate(keys)
                if key not in self._vectors
            ]

            if missing_positions:

                missing_texts = [texts[i] for i in missing_positions]

                new_vectors = np.asarray(
                    encode_function(missing_texts),
                    dtype="float32"
                )

                for position, vector in zip(missing_positions, new_vectors):
                    self._vectors[keys[position]] = vector

            self.last_hits = len(texts) - len(missing_positions)
            self.last_misses = len(missing_positions)

            if not texts:
                return np.zeros((0, 0), dtype="float32")

            matrix = np.vstack(
                [self._vectors[key] for key in keys]
            ).astype("float32")

            try:
                self._save(set(keys))
            except Exception as e:
                # A cache write failure must never break search.
                print("Could not save embedding cache:", str(e))

            return matrix
