from backend.query.pipeline import QueryPipeline


def main():

    pipeline = QueryPipeline()

    while True:

        query = input(
            "\nEnter Query (exit to quit): "
        )

        if query.lower() == "exit":
            break

        processed = pipeline.process(query)

        print()

        print("Processed Query")

        print(processed)


if __name__ == "__main__":
    main()