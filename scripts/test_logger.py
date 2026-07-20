from backend.utils import ProjectLogger


def main():

    logger = ProjectLogger.get_logger()

    logger.info("Application Started")

    logger.debug("Debug message")

    logger.info("Loading Documents")

    logger.info("Building BM25 Index")

    logger.info("Building FAISS Index")

    logger.warning("This is a warning message")

    logger.error("This is an error message")

    logger.critical("This is a critical message")

    logger.info("Application Finished")


if __name__ == "__main__":
    main()