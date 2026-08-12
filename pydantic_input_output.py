from enum import Enum

from flask import jsonify
from pydantic import BaseModel, ConfigDict, Field


class Language(str, Enum):
    polish = "pl"
    english = "en"


class LLMEndpointInputV1(BaseModel):
    response_language: Language

    # author -> message
    prompt_context: list[dict[str, str]]

    prompt: str = Field(max_length=1000)
    user_id: str
    conversation_id: str


class FileUsedV1(BaseModel):
    path: str
    ids_to_highlight: list[str]


class LLMEndpointOutputV1(BaseModel):
    response_language: Language

    prompt: str
    user_id: str
    conversation_id: str

    tk_tokens_used: int

    markdown_response: str
    files_utilized: list[FileUsedV1]

    models_used: dict[str, str]

    @staticmethod
    def mock() -> "LLMEndpointOutputV1":
        return LLMEndpointOutputV1(
            response_language=Language.polish,
            prompt="Mock prompt",
            user_id="user1",
            conversation_id="conversation1",
            tk_tokens_used=2457,
            markdown_response="Na podstawie dostarczonych źródeł, DSM-5 (*Diagnostic and Statistical Manual of Mental Disorders, fifth edition*) to piąta edycja podręcznika wydanego przez American Psychiatric Association (Amerykańskie Towarzystwo Psychiatryczne). Polski tytuł tego opracowania to *Kryteria diagnostyczne zaburzeń psychicznych DSM-5*.\n\nŹródła:\n- SOURCE: 0004.html#item32345\n- SOURCE: 0006.html#item32720",
            files_utilized=[
                FileUsedV1(path="0004.html", ids_to_highlight=["item32345"]),
                FileUsedV1(path="0006.html", ids_to_highlight=["item32720"]),
            ],
            models_used={
                "embedding": "embedding_model",
                "generation": "generation_model",
            },
        )


class ErrorV1(BaseModel):
    http_status_code: int
    message: str


class LLMEndpointErrorOutputV1(BaseModel):
    http_status_code: int
    errors: list[ErrorV1]

    @classmethod
    def from_error_list(
        cls,
        errors: list[ErrorV1],
    ) -> "LLMEndpointErrorOutputV1":
        status_code = max(
            (error.http_status_code for error in errors),
            default=200,
        )

        return cls(
            http_status_code=status_code,
            errors=errors,
        )

    def to_flask_resp(self):
        payload = self.model_dump(exclude={"http_status_code"})

        return jsonify(payload), self.http_status_code
