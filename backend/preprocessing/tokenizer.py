from nltk.tokenize import word_tokenize
import nltk

nltk.download("punkt")
nltk.download("punkt_tab")


class Tokenizer:
    """
    Tokenizes cleaned text.
    """

    def tokenize(self, text: str):  
        return word_tokenize(text)