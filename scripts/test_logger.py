from backend.utils import ProjectLogger


def main():

    logger = ProjectLogger.get_logger()

    logger.info("Project Started")

    logger.info("Loading Documents")

    logger.info("Building BM25")

    logger.info("Building FAISS")

    logger.warning("This is a sample warning.")

    logger.error("This is a sample error.")

    logger.info("Project Finished")


if __name__ == "__main__":
    main()