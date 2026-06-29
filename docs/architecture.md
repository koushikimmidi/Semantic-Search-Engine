# Search Engine Architecture

```text
                User Query
                     │
                     ▼
             Preprocessing
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
      BM25 Search          Dense Search
         │                       │
         └───────────┬───────────┘
                     ▼
         Reciprocal Rank Fusion
                     │
                     ▼
              Ranked Results
```