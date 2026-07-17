from typing import Any, cast

from fastapi import FastAPI, HTTPException
from fastapi.routing import APIRouter
from .schema import AnswerResponse, SearchResult, UserQuery
from .utils import build_context, generate_answer, get_weaviate_client
from .weaviate_client import generate_embedding

router = APIRouter()


@router.get("/")
async def root():
    return {"message": "Ask questions about Django 6.0."}


@router.post("/search", response_model=AnswerResponse)
async def search(query: UserQuery) -> AnswerResponse:
    question = query.query.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    embedding = generate_embedding(question)
   
    if not embedding:
        raise HTTPException(status_code=400, detail="Could not generate an embedding for the query.")

    with get_weaviate_client() as client:
        if not client.collections.exists("Topics"):
            raise HTTPException(status_code=404, detail="Collection 'Topics' does not exist.")

        collection = client.collections.get("Topics")
        res = collection.query.near_vector(near_vector=embedding, limit=4)
        results: list[SearchResult] = []

        for item in res.objects:
            print("res", item.properties)
            properties = cast(dict[str, Any], item.properties)
            title = str(properties.get("title") or "Untitled")
            content = str(properties.get("content") or "")
            source_link = properties.get("source_link")
            url = str(source_link) if source_link else None
            results.append(SearchResult(title=title, url=url, content=content))


    context = build_context(results)
    answer = generate_answer(question, context)
    return AnswerResponse(answer=answer, sources=results)
