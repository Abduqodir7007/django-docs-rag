from pydantic import BaseModel


class UserQuery(BaseModel):
    query: str


class SearchResult(BaseModel):
    title: str
    url: str | None
    content: str


class AnswerResponse(BaseModel):
    answer: str
    sources: list[SearchResult]
