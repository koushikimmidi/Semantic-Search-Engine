from backend.watcher import FolderWatcher


def main():

    watcher = FolderWatcher()

    watcher.start(
        "data/documents"
    )


if __name__ == "__main__":
    main()