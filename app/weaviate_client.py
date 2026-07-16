import os
import json
import weaviate
from weaviate.classes.config import Configure, Property, DataType
from pathlib import Path
from google import genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "en" / "6.0"
CHECKPOINT_FILE = PROJECT_ROOT / "checkpoint.json"

llm = genai.Client(api_key=GEMINI_API_KEY)


def generate_embedding(text: str) -> list[float]:
    if not text.strip():
        return []
    response = llm.models.embed_content(model="gemini-embedding-2", contents=text)
    return response.embeddings[0].values


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> list[str]:
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap

    return chunks


def get_all_json_files() -> list[Path]:
    return sorted(DATA_DIR.rglob("*.json"))


def load_checkpoint() -> Path | None:
    if not CHECKPOINT_FILE.exists():
        return None

    try:
        with CHECKPOINT_FILE.open("r", encoding="utf-8") as file_handle:
            data = json.load(file_handle)
    except OSError, json.JSONDecodeError:
        return None

    last_file = data.get("last_file")
    if not last_file:
        return None

    checkpoint_path = Path(last_file)
    if not checkpoint_path.is_absolute():
        checkpoint_path = (PROJECT_ROOT / checkpoint_path).resolve()

    if not checkpoint_path.exists():
        return None

    return checkpoint_path


def save_checkpoint(file_path: Path) -> None:
    CHECKPOINT_FILE.write_text(
        json.dumps({"last_file": str(file_path.relative_to(PROJECT_ROOT))}, indent=4),
        encoding="utf-8",
    )


def should_skip_file(file_path: Path, checkpoint_file: Path | None) -> bool:
    if checkpoint_file is None:
        return False

    if file_path == checkpoint_file:
        return True

    return file_path <= checkpoint_file


def insert_data_into_weaviate(collection):
    data_files = get_all_json_files()
    checkpoint_file = load_checkpoint()
    resume_processing = checkpoint_file is None

    for file in data_files:
        if not resume_processing:
            if should_skip_file(file, checkpoint_file):
                continue
            resume_processing = True

        with file.open("r", encoding="utf-8") as f:
            data = json.load(f)
            title = data.get("title", "")
            content = data.get("content", "")
            source_link = data.get("url", "")

            chunks = chunk_text(content)

            for chunk in chunks:
                vector = generate_embedding(f"{title}\n\n{chunk}")
                collection.data.insert(
                    properties={"title": title, "content": chunk, "source_link": source_link}, vector=vector
                )

        # Only advance the checkpoint after every chunk from the file has been
        # embedded and inserted successfully. If the process crashes earlier,
        # the file is retried on the next run and no later files are skipped.
        save_checkpoint(file)


with weaviate.connect_to_local() as client:
    if client.collections.exists("Topics"):
        collection = client.collections.get("Topics")
        print("Collection 'Topics' retrieved successfully.")
    else:
        collection = client.collections.create(
            name="Topics",
            vector_config=Configure.Vectors.self_provided(),
            properties=[
                Property(name="title", data_type=DataType.TEXT, description="The title of the topic"),
                Property(name="content", data_type=DataType.TEXT, description="The content of the topic"),
                Property(
                    name="source_link",
                    data_type=DataType.TEXT,
                    description="The source link of the topic",
                ),
            ],
        )
        print("Collection 'Topics' created successfully.")
    insert_data_into_weaviate(collection)
    print("Data inserted into the 'Topics' collection successfully.")

