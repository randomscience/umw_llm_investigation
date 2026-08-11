from dataclasses import asdict, dataclass
import glob
import os
from pathlib import Path
import time
from flask import json
import numpy as np
from typing import Any, Dict, List

from google import genai
from google.genai import types

# klucz mateusz kojro
client = genai.Client(api_key="<>")


EMBEDDING_MODEL = "gemini-embedding-2"
GENERATION_MODEL = "gemini-2.0-flash"

CHUNK_SIZE = 200
CHUNK_OVERLAP = 30


@dataclass
class DocumentChunk:
    chunk_id: str
    file_path: str
    content: str
    embedding: List[float] = None


def load_chunks(path: Path) -> list[DocumentChunk]:
    try:
        with open(path, "r") as fd:
            return [DocumentChunk(**x) for x in json.load(fd)]
    except FileNotFoundError:
        return []


def save_chunks(chunks: List[DocumentChunk], path: Path):

    data = [asdict(x) for x in chunks]

    with open(path, "w") as fd:
        json.dump(data, fd)


class TextFileRAG:
    def __init__(self, chunks=[]):

        self.chunks: List[DocumentChunk] = chunks

    def _chunk_text(self, text: str, file_path: str) -> List[DocumentChunk]:
        """Splits raw text into overlapping chunks based on character count."""

        chunks = []
        start = 0
        chunk_idx = 0

        while start < len(text):
            end = start + CHUNK_SIZE
            chunk_str = text[start:end]

            chunk = DocumentChunk(
                chunk_id=f"{os.path.basename(file_path)}_chunk_{chunk_idx}",
                file_path=file_path,
                content=chunk_str,
            )
            chunks.append(chunk)

            start += CHUNK_SIZE - CHUNK_OVERLAP
            chunk_idx += 1

        return chunks

    def load_directory(self, dir_path: str):

        txt_files = glob.glob(os.path.join(dir_path, "*.html"))

        if not txt_files:
            print(f"No .txt files found in directory: {dir_path}")
            return

        all_chunks = []
        for file_path in txt_files:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
                file_chunks = self._chunk_text(text, file_path)
                all_chunks.extend(file_chunks)

        self.chunks = all_chunks
        print(f"Loaded {len(txt_files)} files into {len(self.chunks)} text chunks.")

    def build_embeddings(self):
        if not self.chunks:
            print("No chunks to embed. Load files first.")
            return

        print("Generating embeddings...")
        contents = [chunk.content for chunk in self.chunks]

        response = client.models.embed_content(model=EMBEDDING_MODEL, contents=contents, 
                                               
                                               ) # Suggested: 768, 1536, or 3072 (default)

        # Assigns vectors to chunks
        for chunk, emb in zip(self.chunks, response.embeddings):
            chunk.embedding = emb.values

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Searches loaded files using cosine similarity against the query embedding."""
        if not self.chunks or self.chunks[0].embedding is None:
            raise ValueError(
                "Index is empty. Please run load_directory and build_embeddings first."
            )

        # Embed the query
        query_response = client.models.embed_content(
            model=EMBEDDING_MODEL, contents=query
        )

        query_vec = np.array(query_response.embeddings[0].values, dtype=np.float32)
        print(query_vec)

        # Compute cosine similarities
        scores = []
        for chunk in self.chunks:
            chunk_vec = np.array(chunk.embedding, dtype=np.float32)

            query_norm = np.linalg.norm(query_vec)
            chunk_norm = np.linalg.norm(chunk_vec)

            if query_norm == 0 or chunk_norm == 0:
                similarity = 0.0
            else:
                similarity = np.dot(query_vec, chunk_vec) / (query_norm * chunk_norm)

            # print(type(similarity), getattr(similarity, "shape", None))

            scores.append((similarity, chunk))

        # Sort descending by score

        scores.sort(key=lambda x: x[0], reverse=True)

        # Format top_k results
        results = []
        for score, chunk in scores[:top_k]:
            results.append(
                {
                    "score": float(score),
                    "file_path": chunk.file_path,
                    "chunk_id": chunk.chunk_id,
                    "content": chunk.content,
                }
            )

        return results

    def generate_answer(self, query: str, top_k: int = 3) -> str:
        """Retrieves relevant text fragments and asks Gemini to generate an answer."""
        search_results = self.search(query, top_k=top_k)

        # Build context string with citations
        context_blocks = []
        for res in search_results:
            source_name = os.path.basename(res["file_path"])
            context_blocks.append(f"[Source: {source_name}]\n{res['content']}")

        context_str = "\n\n---\n\n".join(context_blocks)

        system_instruction = (
            "You are a teacher's assistant. Answer the question accurately using ONLY "
            "the provided context chunks. If the answer is not in the context, explicitly state "
            "that you do not know based on the provided documents. The answer must be simple to understand, ready for using during lessons"
        )

        prompt = f"Context:\n{context_str}\n\nQuestion: {query}"

        # Generate response using client.models.generate_content
        response = client.models.generate_content(
            model=GENERATION_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.2,
            ),
        )

        return response.text, search_results


if __name__ == "__main__":

    docs_dir = Path("templates", "res")

    # load_chunks(Path("./chunks_cache.json"))

    rag = TextFileRAG(load_chunks(Path("./chunks_cache.json")))

    rag.load_directory(docs_dir)
    rag.build_embeddings()

    save_chunks(rag.chunks, Path("./chunks_cache.json"))

    print("RAG ANSWER GENERATION")
    query2 = "What is file about"
    answer, sources = rag.generate_answer(query2, top_k=2)

    print(f"Question: {query2}\n")
    print("Answer:")
    print(answer)
    print("\nRetrieved Context Sources:")
    for s in sources:
        print(f"- {os.path.basename(s['file_path'])} (Score: {s['score']:.4f})")

# if __name__ == "__main__":
#     print("Welcome to Chad GPT - you're own personal jesus")
#     # print(interaction.output_text)
#     while 1 < 2:
#         quarry = input("Ask me anything: ")
#         # resp = client.interactions.create(model="gemini-3.5-flash", input=quarry)
#         # print(resp.output_text)
#         # print(resp.output_text)
