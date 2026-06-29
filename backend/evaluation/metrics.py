import math


def dcg(relevance_scores):
    score = 0.0

    for i, rel in enumerate(relevance_scores):
        score += rel / math.log2(i + 2)

    return score


def ndcg(relevance_scores):
    ideal = sorted(relevance_scores, reverse=True)

    idcg = dcg(ideal)

    if idcg == 0:
        return 0

    return dcg(relevance_scores) / idcg


def reciprocal_rank(relevance_scores):

    for i, rel in enumerate(relevance_scores):

        if rel > 0:
            return 1 / (i + 1)

    return 0