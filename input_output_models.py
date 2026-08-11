from dataclasses import asdict, dataclass
from typing import List

from flask import jsonify
from enum import Enum


class Language(str, Enum):
    polish = "pl"
    english = "en"

    @staticmethod
    def validate(language: str):
        language = language.strip().lower()

        try:
            return Language(language)
        except ValueError:
            return next(iter(Language))


@dataclass
class LLMEndpointInputV1:
    # supported languages: pl
    response_language: Language

    prompt_context: List[
        dict[str:str]  # custom struct  author : message
    ]  # list of prompts / responses user had  # prep json struct

    prompt: str  # max 1000 znaków
    user_id: str
    conversation_id: str  # !important


@dataclass
class FileUsedV1:
    path: str  # <rozdział>/<name>.html  eg. "10/0014.html"
    ids_to_highlight: List[str]  # ["item31989"] can be empty


@dataclass
class LLMEndpointOutputV1:
    # supported languages: pl
    response_language: str

    prompt: str
    user_id: str
    conversation_id: str

    ###
    # for this prompt
    tk_tokens_used: int # "1zł"

    ###
    markdown_response: str
    files_utilized: List[FileUsedV1]

    ###
    models_used: dict[str, str]
    http_status_code: int = 200

    def to_flask_resp(self):
        payload = asdict(self)
        payload.pop("http_status_code")

        return jsonify(payload), self.http_status_code


@dataclass
class ErrorV1:
    http_status_code: int
    message: str


@dataclass
class LLMEndpointErrorOutputV1:
    http_status_code: int
    errors: List[ErrorV1]

    @staticmethod
    def from_error_list(errors: List[ErrorV1]) -> "LLMEndpointErrorOutputV1":
        status_code = 200

        for error in errors:
            if error.http_status_code > status_code:
                status_code = error.http_status_code

        return LLMEndpointErrorOutputV1(status_code, errors)

    def to_flask_resp(self):
        payload = asdict(self)
        payload.pop("http_status_code")

        return jsonify(payload), self.http_status_code
