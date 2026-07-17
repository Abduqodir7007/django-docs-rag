from app.api import router
from fastapi import FastAPI

app = FastAPI(title="Django 6.0 Q&A API", version="1.0.0")
app.include_router(router, prefix="/api", tags=["Q&A"])
