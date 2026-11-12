import os
import threading

from backend.preprocessing.pipeline import PreprocessingPipeline
from backend.retrieval.bm25 import BM25Retriever
from backend.embeddings.encoder import EmbeddingEncoder
from backend.embeddings.indexer import FAISSIndexer
from backend.embeddings.search import SemanticSearcher
from backend.embeddings.chunk_embedding_cache import ChunkEmbeddingCache
from backend.config import Settings
from backend.hybrid.hybrid_search import HybridSearch
from backend.reranker import RerankPipeline
from backend.utils import ProjectLogger
from backend.profiling import PerformanceProfiler
from backend.query.pipeline import QueryPipeline
from backend.filtering import ResultFilter


class SearchEngine:

    def __init__(self, data_path):

        self.data_path = data_path

        self.logger = ProjectLogger.get_logger()
        self.profiler = PerformanceProfiler()

        self.query_pipeline = QueryPipeline()

        self.documents = []
        self.processed_docs = []

        self.bm25 = None
        self.encoder = None
        self.indexer = None
        self.searcher = None
        self.hybrid = None

        self.reranker = None
        self.filter = ResultFilter()

        self.embedding_cache = ChunkEmbeddingCache(
            Settings.EMBEDDING_MODEL,
            cache_file=os.getenv(
                "EMBEDDING_CACHE_PATH",
                "data/index/embedding_cache.pkl"
            )
        )

        # How many fused candidates the cross-encoder rescores.
        self.rerank_candidates = int(
            os.getenv("RERANK_CANDIDATES", "10")
        )

        self.last_query_analysis = {}

        # Searches run on FastAPI worker threads and the automation
        # scheduler thread while uploads/deletes rebuild the index.
        # The lock keeps a search from seeing a half-built index.
        self._lock = threading.RLock()

    def load(self):

        with self._lock:

            self._load()

    def _load(self):

        self.profiler.start("Loading Documents")

        self.logger.info("Loading Documents...")

        pipeline = PreprocessingPipeline(
            self.data_path
        )

        processed_docs = pipeline.process()

        self.profiler.stop("Loading Documents")

        if self.encoder is None:
            self.encoder = EmbeddingEncoder()

        if self.reranker is None:
            self.logger.info("Loading Cross Encoder...")
            self.reranker = RerankPipeline()

        # ----------------------------------------------------
        # Empty knowledge base: BM25 and FAISS cannot be built
        # from zero documents, so search returns no results.
        # ----------------------------------------------------

        if not processed_docs:

            self.logger.warning(
                "Knowledge base is empty. Search will return "
                "no results until documents are added."
            )

            self.processed_docs = []
            self.documents = []
            self.bm25 = None
            self.indexer = None
            self.searcher = None
            self.hybrid = None

            return

        documents = [
            doc["text"]
            for doc in processed_docs
        ]

        tokenized_docs = [
            doc["tokens"]
            for doc in processed_docs
        ]

        self.logger.info("Building BM25...")

        bm25 = BM25Retriever(
            tokenized_docs
        )

        self.profiler.start("Encoding")

        self.logger.info("Encoding Documents...")

        # Only new or changed chunks are encoded; the rest come
        # from the on-disk embedding cache.
        embeddings = self.embedding_cache.encode(
            documents,
            self.encoder.encode
        )

        self.profiler.stop("Encoding")

        self.logger.info(
            f"Embeddings: {self.embedding_cache.last_hits} cached, "
            f"{self.embedding_cache.last_misses} newly encoded"
        )

        self.profiler.start("Building FAISS")

        self.logger.info("Building FAISS Index...")

        indexer = FAISSIndexer(
            embeddings.shape[1],
            metric="cosine"
        )

        indexer.build(
            embeddings
        )

        self.profiler.stop("Building FAISS")

        searcher = SemanticSearcher(
            self.encoder,
            indexer.index,
            normalize=True
        )

        # Spelling correction only suggests words the documents use.
        self.query_pipeline.corrector.update_vocabulary(
            token
            for tokens in tokenized_docs
            for token in tokens
        )

        # Swap in the new index only when it is fully built.
        self.processed_docs = processed_docs
        self.documents = documents
        self.bm25 = bm25
        self.indexer = indexer
        self.searcher = searcher
        self.hybrid = HybridSearch(
            self.bm25,
            self.searcher
        )

        self.logger.info(
            f"Search Engine Ready! ({len(documents)} chunks)"
        )

    def search(
        self,
        query,
        source=None,
        extension=None,
        page=None
    ):

        if not query or not query.strip():
            return []

        with self._lock:

            return self._search(
                query,
                source,
                extension,
                page
            )

    def _search(
        self,
        query,
        source,
        extension,
        page
    ):

        if not self.documents:
            return []

        stages = self.query_pipeline.process(query)

        processed_query = stages["Domain Expanded"] or query

        self.last_query_analysis = stages

        self.logger.info("")
        self.logger.info("=" * 60)
        self.logger.info("QUERY ANALYSIS")
        self.logger.info("=" * 60)

        for stage, value in stages.items():

            self.logger.info(
                f"{stage:<20}: {value}"
            )

        query_tokens = processed_query.lower().split()

        self.profiler.start("BM25 Search")

        bm25_results = self.bm25.search(
            query_tokens,
            top_k=len(self.documents)
        )

        self.profiler.stop("BM25 Search")

        bm25_ids = [
            self.processed_docs[index]["id"]
            for index, score in bm25_results
        ]

        self.profiler.start("Dense Search")

        distances, indices = self.searcher.search(
            processed_query,
            top_k=len(self.documents)
        )

        self.profiler.stop("Dense Search")

        dense_ids = [
            self.processed_docs[index]["id"]
            for index in indices
            if index >= 0
        ]

        self.profiler.start("Hybrid Fusion")

        hybrid_results = self.hybrid.search(
            bm25_ids,
            dense_ids,
            self.processed_docs
        )

        self.profiler.stop("Hybrid Fusion")

        # Optional metadata filters (source / extension / page).
        if source or extension or page:

            hybrid_results = self.filter.filter(
                hybrid_results,
                source=source,
                extension=extension,
                page=page
            )

        self.profiler.start("Cross Encoder")

        # The expanded query helps recall (BM25 + dense), but the
        # cross-encoder judges relevance best on the user's own
        # natural-language question.
        final_results = self.reranker.rerank(
            query.strip(),
            hybrid_results[:self.rerank_candidates]
        )

        self.profiler.stop("Cross Encoder")

        self.profiler.report()

        return final_results
