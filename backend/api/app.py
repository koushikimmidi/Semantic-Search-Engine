from fastapi import FastAPI
from pydantic import BaseModel

from backend.engine.search_engine import SearchEngine
from backend.rag import RAGPipeline


app = FastAPI(
    title="Semantic Intent Search Engine",
    version="1.0.0"
)


engine = SearchEngine(
    "data/raw/sample_documents.json"
)

engine.load()

rag = RAGPipeline()


class SearchRequest(BaseModel):
    query: str


@app.get("/")
def home():

    return {
        "message": "Semantic Intent Search Engine API"
    }


@app.post("/search")
def search(request: SearchRequest):

    results = engine.search(
        request.query
    )

    response = rag.generate_answer(
        request.query,
        results
    )

    return response