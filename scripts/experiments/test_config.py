from backend.config import Settings


def main():

    print("\nPROJECT CONFIGURATION\n")

    print(f"Project Name     : {Settings.PROJECT_NAME}")
    print(f"Version          : {Settings.VERSION}")
    print(f"Dataset Path     : {Settings.DATA_PATH}")
    print(f"Embedding Model  : {Settings.EMBEDDING_MODEL}")
    print(f"Top K            : {Settings.TOP_K}")
    print(f"FAISS Index Path : {Settings.INDEX_PATH}")
    print(f"Ollama Host      : {Settings.OLLAMA_HOST}")
    print(f"Ollama Model     : {Settings.OLLAMA_MODEL}")
    print(f"Log Level        : {Settings.LOG_LEVEL}")


if __name__ == "__main__":
    main()