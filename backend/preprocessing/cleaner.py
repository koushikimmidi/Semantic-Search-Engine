import re


class TextCleaner:
    """
    Cleans raw text before tokenization.
    """

    def clean(self, text: str) -> str:
        # Convert to lowercase
        text = text.lower()

        # Remove punctuation
        text = re.sub(r"[^a-zA-Z0-9\s]", "", text)

        # Remove extra spaces
        text = " ".join(text.split())

        return text