"""
Project Configuration File

All configurable values are stored here.
If you want to change a model, dataset path,
or search settings, modify this file only.
"""


class Settings:

    # ---------------- Dataset ----------------

    DATA_PATH = "data/raw/sample_documents.json"

    # ---------------- Embedding Model ----------------

    EMBEDDING_MODEL = "all-MiniLM-L6-v2"

    # ---------------- Search ----------------

    TOP_K = 5

    # ---------------- FAISS ----------------

    INDEX_PATH = "data/index/faiss.index"

    # ---------------- Project ----------------

    PROJECT_NAME = "Semantic Intent Search Engine"

    VERSION = "1.0.0"