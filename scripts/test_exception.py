from backend.exceptions import *


def main():

    try:

        raise DataFileNotFound(
            "Dataset not found."
        )

    except SearchEngineError as e:

        print()

        print("Custom Exception Caught")

        print(e)


if __name__ == "__main__":
    main()