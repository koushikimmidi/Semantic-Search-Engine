import json
import hashlib
import os


class HashCache:

    def __init__(self):

        self.cache_file = "data/cache/hash_cache.json"

        os.makedirs(
            "data/cache",
            exist_ok=True
        )

        if os.path.exists(self.cache_file):

            with open(
                self.cache_file,
                "r"
            ) as file:

                self.cache = json.load(file)

        else:

            self.cache = {}

    def file_hash(self, file_path):

        hasher = hashlib.md5()

        with open(
            file_path,
            "rb"
        ) as file:

            hasher.update(
                file.read()
            )

        return hasher.hexdigest()

    def is_modified(self, file_path):

        current_hash = self.file_hash(file_path)

        filename = os.path.basename(file_path)

        if filename not in self.cache:

            self.cache[filename] = current_hash

            return True

        if self.cache[filename] != current_hash:

            self.cache[filename] = current_hash

            return True

        return False

    def save(self):

        with open(
            self.cache_file,
            "w"
        ) as file:

            json.dump(
                self.cache,
                file,
                indent=4
            )