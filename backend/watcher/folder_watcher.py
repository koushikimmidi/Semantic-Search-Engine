import time

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from backend.ingestion import IngestionPipeline


class FolderWatcher(FileSystemEventHandler):

    def __init__(self):

        self.pipeline = IngestionPipeline()

        # Debounce settings
        self.last_event_time = 0
        self.debounce_seconds = 2

    def should_process(self):

        current = time.time()

        if current - self.last_event_time < self.debounce_seconds:
            return False

        self.last_event_time = current

        return True

    def on_modified(self, event):

        if event.is_directory:
            return

        if not self.should_process():
            return

        print()
        print("=" * 60)
        print("DOCUMENT MODIFIED")
        print("=" * 60)

        print(event.src_path)

        self.pipeline.build(
            "data/documents"
        )

    def on_created(self, event):

        if event.is_directory:
            return

        if not self.should_process():
            return

        print()
        print("=" * 60)
        print("NEW DOCUMENT")
        print("=" * 60)

        print(event.src_path)

        self.pipeline.build(
            "data/documents"
        )

    def start(self, folder):

        observer = Observer()

        observer.schedule(
            self,
            folder,
            recursive=False
        )

        observer.start()

        print()
        print("=" * 60)
        print("WATCHING DOCUMENT FOLDER...")
        print("=" * 60)
        print("Press Ctrl + C to stop watching.")
        print("=" * 60)

        try:

            while True:
                time.sleep(1)

        except KeyboardInterrupt:

            print()
            print("Stopping Folder Watcher...")

            observer.stop()

        observer.join()