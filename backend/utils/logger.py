import logging


class ProjectLogger:

    @staticmethod
    def get_logger():

        logger = logging.getLogger("SemanticSearch")

        if not logger.handlers:

            logger.setLevel(logging.INFO)

            formatter = logging.Formatter(
                "[%(levelname)s] %(message)s"
            )

            console_handler = logging.StreamHandler()

            console_handler.setFormatter(
                formatter
            )

            logger.addHandler(
                console_handler
            )

        return logger