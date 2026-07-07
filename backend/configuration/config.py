import os

from dotenv import load_dotenv


load_dotenv()


class Config:

    OLLAMA_HOST = os.getenv(
        "OLLAMA_HOST",
        "http://127.0.0.1:11434"
    )

    OLLAMA_MODEL = os.getenv(
        "OLLAMA_MODEL",
        "gemma4:latest"
    )

    DOCUMENT_PATH = os.getenv(
        "DOCUMENT_PATH",
        "data/raw/sample_documents.json"
    )

    VECTOR_DIMENSION = int(

        os.getenv(
            "VECTOR_DIMENSION",
            "384"
        )

    )

    LOG_LEVEL = os.getenv(
        "LOG_LEVEL",
        "INFO"
    )