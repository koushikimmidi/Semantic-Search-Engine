import logging
import os

from backend.config import Settings


class ProjectLogger:

    _logger = None

    @classmethod
    def get_logger(cls):

        if cls._logger is not None:
            return cls._logger

        os.makedirs(
            "logs",
            exist_ok=True
        )

        logger = logging.getLogger(
            Settings.PROJECT_NAME
        )

        logger.setLevel(
            getattr(
                logging,
                Settings.LOG_LEVEL.upper(),
                logging.INFO
            )
        )

        logger.handlers.clear()

        formatter = logging.Formatter(

            "%(asctime)s | %(levelname)s | %(message)s",

            "%Y-%m-%d %H:%M:%S"

        )

        # ---------------- Console ----------------

        console = logging.StreamHandler()

        console.setFormatter(
            formatter
        )

        # ---------------- File ----------------

        file_handler = logging.FileHandler(
            "logs/application.log",
            encoding="utf-8"
        )

        file_handler.setFormatter(
            formatter
        )

        logger.addHandler(console)

        logger.addHandler(file_handler)

        cls._logger = logger

        return logger