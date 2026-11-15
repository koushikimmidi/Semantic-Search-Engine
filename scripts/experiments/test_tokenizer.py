from backend.preprocessing.cleaner import TextCleaner
from backend.preprocessing.tokenizer import Tokenizer

def main():
    cleaner = TextCleaner()
    tokenizer = Tokenizer()

    sentence = "Machine Learning is AWESOME!!!"

    cleaned = cleaner.clean(sentence)
    tokens = tokenizer.tokenize(cleaned)

    print("Original :", sentence)
    print("Cleaned  :", cleaned)
    print("Tokens   :", tokens)

if __name__ == "__main__":
    main()