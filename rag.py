import hashlib
import json
import logging
from pathlib import Path

import numpy as np
from bs4 import BeautifulSoup
from bs4.builder import HTML, HTML_5
from google import genai

from prompt import get_prompt

logger = logging.getLogger(__name__)


def parse_documents(files_path, min_text_length):
    documents = []

    for file_index, path in enumerate(files_path.rglob("*.html")):

        soup = BeautifulSoup(
            path.read_text(encoding="utf-8"),
            "html.parser",
        )

        for div_index, div in enumerate(soup.find_all("div", id=True)):

            if not str(div["id"]).startswith("item"):
                continue

            text = div.get_text(" ", strip=True)

            if not text or len(text.strip()) < min_text_length:
                continue

            documents.append(
                {
                    "text": text,
                    "file": str(path.relative_to(files_path)),
                    "div_id": div["id"],
                }
            )

    logger.info(f"Loaded {len(documents)} HTML sections")

    return documents


def load_embedding_cache(cache_file):
    if not cache_file.exists():
        logger.info("No embedding cache found.")
        return {}

    with cache_file.open("r", encoding="utf-8") as f:
        cache = json.load(f)

    logger.info(f"Loaded {len(cache)} cached embeddings")

    return cache


def save_embedding_cache(cache, cache_file):
    with cache_file.open("w", encoding="utf-8") as f:
        json.dump(cache, f)


def get_embedding_cache_key(doc, embedding_model):
    content = (
        f"{embedding_model}|" f"{doc['file']}|" f"{doc['div_id']}|" f"{doc['text']}"
    )

    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def create_embedding(client, text, model):
    result = client.models.embed_content(
        model=model,
        contents=text,
    )

    return np.array(
        result.embeddings[0].values,
        dtype=np.float32,
    )


def create_embeddings_for_documents(client, documents, embedding_model, cache_file):
    cache = load_embedding_cache(cache_file)

    cached_count = 0
    api_count = 0

    for i, doc in enumerate(documents):
        cache_key = get_embedding_cache_key(doc, embedding_model)

        if cache_key in cache:
            doc["embedding"] = np.array(
                cache[cache_key],
                dtype=np.float32,
            )
            cached_count += 1
        else:
            embedding = create_embedding(client, doc["text"], embedding_model)
            doc["embedding"] = embedding
            cache[cache_key] = embedding.tolist()

            save_embedding_cache(cache, cache_file)
            api_count += 1

    logger.info(f"Loaded embeddings: Cached: {cached_count}, API: {api_count}")

    return documents


def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def calculate_scores(documents, query_embedding):
    for doc in documents:
        doc["score"] = cosine_similarity(
            query_embedding,
            doc["embedding"],
        )


def get_top_k(documents, k):
    return sorted(
        documents,
        key=lambda x: x["score"],
        reverse=True,
    )[:k]


def load_or_generate_embeddings(
    client, dir, min_text_length, embedding_model, cache_file
):
    documents = parse_documents(dir, min_text_length)
    documents = create_embeddings_for_documents(
        client, documents, embedding_model, cache_file
    )
    return documents


def get_sources(client, query, documents, k, embedding_model):
    query_embedding = create_embedding(client, query, embedding_model)
    calculate_scores(documents, query_embedding)
    retrieved = get_top_k(documents, k)
    return retrieved


def generate_content(client, prompt, generation_model):
    response = client.models.generate_content(
        model=generation_model,
        contents=prompt,
    )
    return response


class RAGClient:

    def __init__(
        self, client, documents_dir, model, embedding_model, min_text_length, cache_file
    ):
        self.client = client
        self.documents = load_or_generate_embeddings(
            client, documents_dir, min_text_length, embedding_model, cache_file
        )
        self.model = model
        self.embedding_model = embedding_model

    def get_sources(self, query, k):
        query_embedding = create_embedding(self.client, query, self.embedding_model)
        calculate_scores(self.documents, query_embedding)
        retrieved = get_top_k(self.documents, k)
        return retrieved

    def generate_content(self, prompt):
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
        )
        return response


def main():
    import os
    from dotenv import load_dotenv
    from logging_config import setup_logging
    setup_logging()
    load_dotenv()

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    HTML_DIR = Path("templates/10")
    GENERATION_MODEL = "gemini-3.6-flash"
    EMBEDDING_MODEL = "gemini-embedding-2"
    MIN_TEXT_LENGTH = 200
    CACHE_FILE = Path("embedding_cache.json")

    rag = RAGClient(
        client, HTML_DIR, GENERATION_MODEL, EMBEDDING_MODEL, MIN_TEXT_LENGTH, CACHE_FILE
    )

    query = input("\nQuestion: ")
    retrieved = rag.get_sources(query, k=5)
    prompt = get_prompt(query, retrieved, "pl")
    response = rag.generate_content(prompt)

    print(response.text)


if __name__ == "__main__":
    main()
