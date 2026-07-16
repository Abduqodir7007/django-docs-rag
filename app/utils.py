import os

import weaviate

from .schema import SearchResult
from .weaviate_client import llm


def get_weaviate_client():
    return weaviate.connect_to_custom(
        http_host=os.getenv("WEAVIATE_HTTP_HOST", "weaviate"),
        http_port=int(os.getenv("WEAVIATE_HTTP_PORT", "8080")),
        http_secure=os.getenv("WEAVIATE_HTTP_SECURE", "false").lower() == "true",
        grpc_host=os.getenv("WEAVIATE_GRPC_HOST", "weaviate"),
        grpc_port=int(os.getenv("WEAVIATE_GRPC_PORT", "50051")),
        grpc_secure=os.getenv("WEAVIATE_GRPC_SECURE", "false").lower() == "true",
        skip_init_checks=True,
    )


def build_context(results: list[SearchResult]) -> str:
    if not results:
        return "No relevant context was found in the vector database."

    formatted_results = []
    for result in results:
        source_line = f"Source: {result.url}" if result.url else "Source: unknown"
        formatted_results.append(
            "\n".join(
                [
                    f"Title: {result.title}",
                    source_line,
                    f"Content: {result.content}",
                ]
            )
        )

    return "\n\n---\n\n".join(formatted_results)


def generate_answer(question: str, context: str) -> str:
    prompt = f"""You are a precise assistant for questions about Django 6.0.

Use only the context below to answer the question. If the context does not contain the answer,
say that you could not find it in the indexed Django 6.0 documentation.

Context:
{context}

Question: {question}

Answer in a helpful, concise way."""

    response = llm.models.generate_content(model="gemini-2.0-flash", contents=prompt)
    text = getattr(response, "text", None)
    if isinstance(text, str) and text.strip():
        return text.strip()

    candidates = getattr(response, "candidates", None) or []
    for candidate in candidates:
        content = getattr(candidate, "content", None)
        parts = getattr(content, "parts", None) or []
        for part in parts:
            part_text = getattr(part, "text", None)
            if isinstance(part_text, str) and part_text.strip():
                return part_text.strip()

    raise ValueError("Gemini returned an empty answer.")
