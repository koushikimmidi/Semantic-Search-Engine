from backend.config import JsonConfig


def main():

    config = JsonConfig(
        "config/settings.json"
    )

    print()

    print("PROJECT CONFIGURATION")

    print("-" * 40)

    print("Project :", config.project_name)

    print("Version :", config.version)

    print("Dataset :", config.dataset_path)

    print("Embedding Model :", config.embedding_model)

    print("Top K :", config.top_k)

    print("FAISS :", config.faiss_index)


if __name__ == "__main__":
    main()