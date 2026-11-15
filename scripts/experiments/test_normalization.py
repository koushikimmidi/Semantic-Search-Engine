from backend.query.pipeline import QueryPipeline


def main():

    pipeline = QueryPipeline()

    while True:

        query = input(
            "\nEnter Query (exit to quit): "
        )

        if query.lower() == "exit":

            break

        result = pipeline.process(query)

        print()

        print("Processed Query")

        print(result)

        print()


if __name__ == "__main__":

    main()