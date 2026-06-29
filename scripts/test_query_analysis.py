from backend.query.pipeline import QueryPipeline


def main():

    pipeline = QueryPipeline()

    while True:

        query = input("\nEnter Query (exit to quit): ")

        if query.lower() == "exit":
            break

        stages = pipeline.process(query)

        print("\n" + "=" * 60)
        print("QUERY ANALYSIS")
        print("=" * 60)

        for stage, value in stages.items():

            print(f"{stage:<20}: {value}")


if __name__ == "__main__":
    main()