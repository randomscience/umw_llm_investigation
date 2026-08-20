import logging
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from google import genai
from starlette.requests import Request

from logging_config import setup_logging
from prompt import get_prompt
from pydantic_input_output import FileUsedV1 as LLMHighlight
from pydantic_input_output import LLMEndpointInputV1 as LLMRequest
from pydantic_input_output import LLMEndpointOutputV1 as LLMResponse
from rag import RAGClient
from google.genai._gaos.lib.compat_errors import BadRequestError as GemminiBadRequest

setup_logging()
logger = logging.getLogger(__name__)

load_dotenv()

API_TOKENS = os.environ.get("API_TOKENS", "").split(",")
HTML_DIR = Path(os.environ.get("BOOK_DIR", "templates/10"))
GENERATION_MODEL = os.environ.get("GENERATION_MODEL", "gemini-3.6-flash")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "gemini-embedding-2")
MIN_TEXT_LENGTH = int(os.environ.get("MIN_TEXT_LENGTH", 200))
CACHE_FILE = Path(os.environ.get("CACHE_FILE", "embedding_cache.json"))

app = FastAPI(title="UMW LLM", version="0.1.0")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        "Unhandled exception: %s %s (%s)",
        request.method,
        request.url,
        exc,
        stack_info=True,
    )

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
):
    if credentials.credentials not in API_TOKENS:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
        )

    return credentials.credentials


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()

    response = await call_next(request)

    duration = time.perf_counter() - start

    logger.info(
        "%s %s -> %d (%.3fs)",
        request.method,
        request.url.path,
        response.status_code,
        duration,
    )

    return response


@app.get("/v1/status")
def status():
    return {"status": "ok"}


@app.post("/v1/rag", response_model=LLMResponse, dependencies=[Depends(verify_token)])
def rag(llm_request: LLMRequest, mock: bool = False) -> LLMResponse:

    if mock:
        return LLMResponse.mock()

    client = genai.Client()

    rag = RAGClient(
        client, HTML_DIR, GENERATION_MODEL, EMBEDDING_MODEL, MIN_TEXT_LENGTH, CACHE_FILE
    )

    try:
        retrieved = rag.get_sources(llm_request.prompt, k=5)
        prompt = get_prompt(llm_request.prompt, retrieved, llm_request.response_language)
        response = rag.generate_content(prompt, llm_request.previous_message_id)

        return LLMResponse(
            response_language=llm_request.response_language,
            prompt=llm_request.prompt,
            user_id=llm_request.user_id,
            conversation_id=llm_request.conversation_id,
            message_id=response.id,
            tk_tokens_used=response.usage.total_tokens,
            markdown_response=response.output_text,
            files_utilized=[
                LLMHighlight(
                    path=doc["file"],
                    ids_to_highlight=[doc["div_id"]],
                )
                for doc in retrieved
            ],
            models_used={"embedding": EMBEDDING_MODEL, "generation": GENERATION_MODEL},
        )
    except GemminiBadRequest as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Server error")
