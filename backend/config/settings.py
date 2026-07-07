"""
Project Configuration

Reads configuration from .env.
Falls back to default values if a variable
is not present.
"""

import os

from dotenv import load_dotenv


load_dotenv()


class Settings:

    # ---------------- Project ----------------

    PROJECT_NAME = os.getenv(
        "PROJECT_NAME",
        "Semantic Intent Search Engine"
    )

    VERSION = os.getenv(
        "VERSION",
        "1.0.0"
    )

    # ---------------- Dataset ----------------

    DATA_PATH = os.getenv(
        "DATA_PATH",
        "data/raw/sample_documents.json"
    )

    # ---------------- Embedding ----------------

    EMBEDDING_MODEL = os.getenv(
        "EMBEDDING_MODEL",
        "all-MiniLM-L6-v2"
    )

    # ---------------- Search ----------------

    TOP_K = int(
        os.getenv(
            "TOP_K",
            "5"
        )
    )

    # ---------------- FAISS ----------------

    INDEX_PATH = os.getenv(
        "INDEX_PATH",
        "data/index/faiss.index"
    )

    # ---------------- Ollama ----------------

    OLLAMA_HOST = os.getenv(
        "OLLAMA_HOST",
        "http://127.0.0.1:11434"
    )

    OLLAMA_MODEL = os.getenv(
        "OLLAMA_MODEL",
        "gemma4:latest"
    )

    # ---------------- Logging ----------------

    LOG_LEVEL = os.getenv(
        "LOG_LEVEL",
        "INFO"
    )