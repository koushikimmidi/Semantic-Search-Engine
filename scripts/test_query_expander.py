from backend.query import QueryExpander


def main():

    expander = QueryExpander()

    while True:

        query = input(
            "Enter Query (exit to quit): "
        )

        if query.lower() == "exit":
            break

        expanded = expander.expand(query)

        print()

        print("Original :", query)

        print("Expanded :", expanded)

        print()


if __name__ == "__main__":
    main()