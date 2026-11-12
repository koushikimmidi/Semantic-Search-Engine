from nltk.tokenize import word_tokenize
import nltk


def _ensure_nltk_resource(resource_path, package):
    """
    Download an NLTK resource only when it is missing, so the API
    starts quickly and works offline once the data is present.
    """

    try:
        nltk.data.find(resource_path)
    except LookupError:
        nltk.download(package, quiet=True)


_ensure_nltk_resource("tokenizers/punkt", "punkt")
_ensure_nltk_resource("tokenizers/punkt_tab", "punkt_tab")


class Tokenizer:
    """
    Tokenizes cleaned text.
    """

    def tokenize(self, text: str):
        return word_tokenize(text)
