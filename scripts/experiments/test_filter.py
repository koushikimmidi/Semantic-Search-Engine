from backend.filtering import ResultFilter


def main():

    documents = [

        {
            "text": "Artificial Intelligence",

            "source": "AI.txt",

            "page": 1
        },

        {
            "text": "Machine Learning",

            "source": "ML.pdf",

            "page": 2
        },

        {
            "text": "Deep Learning",

            "source": "DL.pdf",

            "page": 1
        },

        {
            "text": "Python",

            "source": "Python.txt",

            "page": 3
        }

    ]

    filter_engine = ResultFilter()

    print()

    print("=" * 60)
    print("TXT FILES")
    print("=" * 60)

    txt = filter_engine.filter(

        documents,

        extension=".txt"

    )

    for document in txt:

        print(document)

    print()

    print("=" * 60)
    print("PAGE 1")
    print("=" * 60)

    page = filter_engine.filter(

        documents,

        page=1

    )

    for document in page:

        print(document)
        

    print()

    print("=" * 60)
    print("SOURCE = AI.txt")
    print("=" * 60)

    source = filter_engine.filter(

        documents,

        source="AI.txt"

    )

    for document in source:

        print(document)


if __name__ == "__main__":
    main()