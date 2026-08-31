import hashlib
import json
import logging
import os
import time
from pathlib import Path

import numpy as np
from bs4 import BeautifulSoup
from bs4.builder import HTML, HTML_5
from google import genai
from google.genai import errors

from prompt import get_prompt

logger = logging.getLogger(__name__)

EMBEDDING_BATCH_SIZE = 32
TRANSIENT_ERROR_CODES = {408, 429, 500, 502, 503, 504}


def parse_documents(files_path, min_text_length):
    documents = []

    for path in files_path.rglob("*.html"):

        soup = BeautifulSoup(
            path.read_text(encoding="utf-8"),
            "html.parser",
        )

        for div in soup.find_all("div", id=True):

            if not str(div["id"]).startswith("item"):
                continue

            text = div.get_text(" ", strip=True)

            # Page number comes from the file name (e.g. 865.html -> page 865)
            # instead of the enumeration index, which depends on the traversal
            # order and would invalidate the whole embedding cache on any change.
            text = f"Na stronie {path.stem} napisane jest: " + text

            if not text or len(text.strip()) < min_text_length:
                continue

            documents.append(
                {
                    "text": text,
                    # POSIX separators keep the embedding cache key
                    # platform-independent (Windows vs Linux)
                    "file": path.relative_to(files_path).as_posix(),
                    "div_id": div["id"],
                }
            )

    logger.info(f"Loaded {len(documents)} HTML sections")

    return documents


def load_embedding_cache(cache_file):
    if not cache_file.exists():
        logger.info("No embedding cache found.")
        return {}

    try:
        with cache_file.open("r", encoding="utf-8") as f:
            cache = json.load(f)
    except json.JSONDecodeError:
        logger.warning(
            "Embedding cache is corrupted (%s); rebuilding it.",
            cache_file,
        )
        return {}

    logger.info(f"Loaded {len(cache)} cached embeddings")

    return cache


def save_embedding_cache(cache, cache_file):
    # Write atomically so an interrupted process never leaves a
    # truncated JSON file that invalidates the whole cache.
    tmp_file = cache_file.with_name(cache_file.name + ".tmp")
    with tmp_file.open("w", encoding="utf-8") as f:
        json.dump(cache, f)
    os.replace(tmp_file, cache_file)


def get_embedding_cache_key(doc, embedding_model):
    content = (
        f"{embedding_model}|" f"{doc['file']}|" f"{doc['div_id']}|" f"{doc['text']}"
    )

    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def create_embeddings(client, texts, model, retries=5, base_delay=2.0):
    # gemini-embedding-2 aggregates plain strings into a single embedding.
    # Wrapping each text in a Content object returns one embedding per input.
    contents = [genai.types.Content(parts=[genai.types.Part(text=t)]) for t in texts]

    last_error = None
    for attempt in range(retries):
        try:
            result = client.models.embed_content(model=model, contents=contents)
            embeddings = [
                np.array(emb.values, dtype=np.float32) for emb in result.embeddings
            ]
            if len(embeddings) != len(texts):
                raise RuntimeError(
                    f"Expected {len(texts)} embeddings, got {len(embeddings)}"
                )
            return embeddings
        except errors.APIError as e:
            if e.code not in TRANSIENT_ERROR_CODES:
                raise
            last_error = e
            delay = base_delay * (2**attempt)
            logger.warning(
                "Embedding API error (%s), retrying in %.1fs",
                e.code,
                delay,
            )
            time.sleep(delay)

    raise last_error


def create_embedding(client, text, model):
    return create_embeddings(client, [text], model)[0]


def create_embeddings_for_documents(
    client,
    documents,
    embedding_model,
    cache_file,
    batch_size=EMBEDDING_BATCH_SIZE,
):
    cache = load_embedding_cache(cache_file)

    cached_count = 0
    pending = []

    for doc in documents:
        cache_key = get_embedding_cache_key(doc, embedding_model)

        if cache_key in cache:
            doc["embedding"] = np.array(
                cache[cache_key],
                dtype=np.float32,
            )
            cached_count += 1
        else:
            pending.append((doc, cache_key))

    for start in range(0, len(pending), batch_size):
        chunk = pending[start : start + batch_size]
        embeddings = create_embeddings(
            client,
            [doc["text"] for doc, _ in chunk],
            embedding_model,
        )
        for (doc, cache_key), embedding in zip(chunk, embeddings):
            doc["embedding"] = embedding
            cache[cache_key] = embedding.tolist()

    save_embedding_cache(cache, cache_file)

    logger.info(
        f"Loaded embeddings: Cached: {cached_count}, API: {len(pending)}"
    )

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

    def generate_content(self, prompt, conversation_id):
        response = self.client.interactions.create(
            model=self.model,
            input=prompt,
            previous_interaction_id=conversation_id,
        )
        return response


def main():
    import os
    from dotenv import load_dotenv
    from logging_config import setup_logging
    setup_logging()
    load_dotenv()

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    HTML_DIR = Path("templates/export_parsed")
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
    response = rag.generate_content(prompt, None)

    print(response.text)


if __name__ == "__main__":
    main()
