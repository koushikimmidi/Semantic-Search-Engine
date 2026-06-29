# Week 2 Analysis

---

# Query 1 : AI

## BM25

Returned:Machine Learning is a subset of Artificial Intelligence.
Score:0.0000
Observation:The query was "AI", but none of the documents contain the exact keyword "AI". BM25 performs keyword matching, so all documents received a score of 0.0. Since every score was identical, the documents were returned in their original order.

## Dense Retrieval

Returned:Machine Learning is a subset of Artificial Intelligence.
Distance:0.9948
Observation:Dense Retrieval correctly understood that "AI" and "Artificial Intelligence" have the same semantic meaning. It retrieved the most relevant document even though the exact keyword "AI" was not present.

Winner:Dense Retrieval

---

# Query 2 : Artificial Intelligence

## BM25

Returned:Machine Learning is a subset of Artificial Intelligence.
Score:2.1464
Observation:BM25 successfully retrieved the correct document because the exact keywords "Artificial" and "Intelligence" are present in the document. Since there was an exact keyword match, it assigned a high relevance score.

## Dense Retrieval

Returned:Machine Learning is a subset of Artificial Intelligence.
Distance:0.8418
Observation:Dense Retrieval also retrieved the correct document by understanding the semantic meaning of the query. It produced the lowest distance among all retrieved documents, indicating the highest similarity.

Winner:Tie (Both BM25 and Dense Retrieval performed equally well for this query because the exact keywords were present and the semantic meaning also matched.)

---

# Query 3 : Machine Learning

## BM25

Returned:Machine Learning is a subset of Artificial Intelligence.
Score:1.4019
Observation:BM25 successfully retrieved the correct document because the exact keywords "Machine" and "Learning" are present in the document. It assigned the highest score to the most relevant document, while documents with fewer matching keywords received lower scores.

## Dense Retrieval

Returned:Machine Learning is a subset of Artificial Intelligence.
Distance:0.8303
Observation:Dense Retrieval correctly identified the most semantically similar document. It produced the lowest distance, indicating that the document is highly relevant to the query based on meaning rather than only exact keyword matching.

Winner:Tie (Both BM25 and Dense Retrieval returned the same top-ranked document. BM25 succeeded because of exact keyword matching, while Dense Retrieval succeeded because of semantic similarity.)

---

# Query 4 : Deep Learning

## BM25

Returned:Neural networks are a core part of deep learning.
Score:1.3252
Observation:BM25 successfully retrieved the most relevant document because it contains the exact keywords "Deep" and "Learning". The second-ranked document discusses Machine Learning, which is related but less relevant.

## Dense Retrieval

Returned:Neural networks are a core part of deep learning.
Distance:0.7609
Observation:Dense Retrieval correctly identified the document discussing Deep Learning. It achieved the lowest distance, showing that it understands the semantic relationship between Deep Learning and Neural Networks.

Winner:Tie (Both BM25 and Dense Retrieval returned the correct top-ranked document. BM25 relied on exact keyword matching, while Dense Retrieval relied on semantic understanding.)


---

# Query 5 : Python

## BM25

Returned:Python is widely used in Data Science.
Score:0.3489
Observation:BM25 ranked the document containing the exact keyword "Python" as the highest result. The FastAPI document appeared second because it also contains the word "Python".


## Dense Retrieval

Returned:Python is widely used in Data Science.
Distance:0.6574
Observation:Dense Retrieval also ranked the Python-related document first. It correctly understood the semantic meaning of the query and retrieved the most relevant document.

Winner:Tie (Both BM25 and Dense Retrieval successfully retrieved the most relevant Python-related document.)

---

# Query 6 : BM25

## BM25

Returned:BM25 is a keyword ranking algorithm.
Score:1.2136
Observation:BM25 ranked the correct document at the top because the query exactly matched the keyword "BM25". This demonstrates the strength of keyword-based retrieval.

## Dense Retrieval

Returned:BM25 is a keyword ranking algorithm.
Distance:0.8788
Observation:Dense Retrieval also retrieved the correct document as the top result. Although it uses semantic embeddings rather than keyword matching, it successfully identified the relevant document.

Winner:Tie (Both BM25 and Dense Retrieval correctly retrieved the BM25 document as the top-ranked result.)