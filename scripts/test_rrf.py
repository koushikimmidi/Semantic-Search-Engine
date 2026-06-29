from backend.hybrid.rrf import ReciprocalRankFusion


def main():

    bm25_results = [
        1,
        2,
        3,
        4,
        5
    ]

    dense_results = [
        3,
        1,
        5,
        2,
        4
    ]

    rrf = ReciprocalRankFusion()

    fused = rrf.fuse(
        [
            bm25_results,
            dense_results
        ]
    )

    print("\nHybrid Ranking\n")

    for rank, (doc_id, score) in enumerate(fused, start=1):

        print(
            f"{rank}. "
            f"Document {doc_id} "
            f"Score = {score:.6f}"
        )


if __name__ == "__main__":
    main()