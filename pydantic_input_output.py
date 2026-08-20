from enum import Enum
from typing import Optional

from flask import jsonify
from pydantic import BaseModel, ConfigDict, Field, field_validator


class Language(str, Enum):
    polish = "pl"
    english = "en"


class LLMEndpointInputV1(BaseModel):
    response_language: Language

    # author -> message
    prompt_context: list[dict[str, str]]

    prompt: str = Field(max_length=1000)
    user_id: str
    conversation_id: str | None
    previous_message_id: str | None = Field(default=None, json_schema_extra={"default": None})

    @field_validator("previous_message_id")
    @classmethod
    def validate_version(cls, value):
        if value is not None and not value.startswith("v1"):
            raise ValueError("previous_message_id must come from the previous invocation of the API")
        return value

class FileUsedV1(BaseModel):
    path: str
    ids_to_highlight: list[str]


class LLMEndpointOutputV1(BaseModel):
    response_language: Language

    prompt: str
    user_id: str
    conversation_id: str
    message_id: str = Field(pattern=r"^v1")

    tk_tokens_used: int

    markdown_response: str
    files_utilized: list[FileUsedV1]

    models_used: dict[str, str]

    @staticmethod
    def mock() -> "LLMEndpointOutputV1":
        return LLMEndpointOutputV1(
            response_language=Language.polish,
            prompt="Mock prompt",
            user_id="mock_user_id",
            conversation_id="mock_conversation_id",
            message_id="v1_mock_message_id",
            tk_tokens_used=2457,
            markdown_response="Mock markdown response: Na podstawie dostarczonych źródeł, DSM-5 (*Diagnostic and Statistical Manual of Mental Disorders, fifth edition*) to piąta edycja podręcznika wydanego przez American Psychiatric Association (Amerykańskie Towarzystwo Psychiatryczne). Polski tytuł tego opracowania to *Kryteria diagnostyczne zaburzeń psychicznych DSM-5*.\n\nŹródła:\n- SOURCE: 0004.html#item32345\n- SOURCE: 0006.html#item32720",
            files_utilized=[
                FileUsedV1(path="0004.html", ids_to_highlight=["item32345"]),
                FileUsedV1(path="0006.html", ids_to_highlight=["item32720"]),
            ],
            models_used={
                "embedding": "mock_embedding_model",
                "generation": "mock_generation_model",
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
