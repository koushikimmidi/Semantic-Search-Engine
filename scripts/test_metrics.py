from backend.evaluation.metrics import ndcg, reciprocal_rank


relevance = [1,0,1,0,0]

print("NDCG :", ndcg(relevance))
print("MRR  :", reciprocal_rank(relevance))