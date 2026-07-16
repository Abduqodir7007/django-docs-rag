import weaviate
from fastapi import FastAPI


app = FastAPI()

@app.get("/")
async def root():
    pass

with weaviate.connect_to_local() as client:
    collection = client.collections.get("Topics")
    res = collection.query.near_vector()