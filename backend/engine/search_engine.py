from backend.preprocessing.pipeline import PreprocessingPipeline
from backend.retrieval.bm25 import BM25Retriever
from backend.embeddings.encoder import EmbeddingEncoder
from backend.embeddings.indexer import FAISSIndexer
from backend.embeddings.search import SemanticSearcher
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

        self.documents = None
        self.processed_docs = None

        self.bm25 = None
        self.encoder = None
        self.indexer = None
        self.searcher = None
        self.hybrid = None

        self.reranker = None
        self.filter = ResultFilter()

    def load(self):

        self.profiler.start("Loading Documents")

        self.logger.info("Loading Documents...")

        pipeline = PreprocessingPipeline(
            self.data_path
        )

        self.processed_docs = pipeline.process()

        self.documents = [
            doc["text"]
            for doc in self.processed_docs
        ]

        tokenized_docs = [
            doc["tokens"]
            for doc in self.processed_docs
        ]

        self.profiler.stop("Loading Documents")

        self.logger.info("Building BM25...")

        self.bm25 = BM25Retriever(
            tokenized_docs
        )

        self.profiler.start("Encoding")

        self.logger.info("Encoding Documents...")

        self.encoder = EmbeddingEncoder()

        embeddings = self.encoder.encode(
            self.documents
        )

        self.profiler.stop("Encoding")

        self.profiler.start("Building FAISS")

        self.logger.info("Building FAISS Index...")

        self.indexer = FAISSIndexer(
            embeddings.shape[1]
        )

        self.indexer.build(
            embeddings
        )

        self.profiler.stop("Building FAISS")

        self.searcher = SemanticSearcher(
            self.encoder,
            self.indexer.index
        )

        self.hybrid = HybridSearch(
            self.bm25,
            self.searcher
        )

        self.logger.info("Loading Cross Encoder...")

        self.reranker = RerankPipeline()

        self.logger.info("Search Engine Ready!")

    def search(
        self,
        query,
        source=None,
        extension=None,
        page=None
    ):

        stages = self.query_pipeline.process(query)

        processed_query = stages["Domain Expanded"]

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
        ]

        self.profiler.start("Hybrid Fusion")

        hybrid_results = self.hybrid.search(
            bm25_ids,
            dense_ids,
            self.processed_docs
        )

        self.profiler.stop("Hybrid Fusion")

        self.profiler.start("Cross Encoder")

        final_results = self.reranker.rerank(
            processed_query,
            hybrid_results
        )

        self.profiler.stop("Cross Encoder")

        # =====================================================
        # TEMPORARY DEBUG (REMOVE AFTER TESTING)
        # =====================================================

        print()
        print("=" * 60)
        print("FINAL RESULTS STRUCTURE")
        print("=" * 60)

        for result in final_results:
            print(result)

        print("=" * 60)

        # =====================================================

        # Temporarily return without filtering
        self.profiler.report()

        return final_results