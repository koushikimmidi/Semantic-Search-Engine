from backend.query.pipeline import QueryPipeline
from backend.evaluation.search_evaluator import SearchEvaluator


def main():

    pipeline = QueryPipeline()

    evaluator = SearchEvaluator()

    while True:

        query = input("\nEnter Query (exit to quit): ")

        if query.lower() == "exit":
            break

        stages = pipeline.process(query)

        evaluator.compare(
            query,
            stages["Domain Expanded"]
        )


if __name__ == "__main__":
    main()