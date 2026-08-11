from dotenv import load_dotenv
load_dotenv()

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
from typing import List, Tuple
from flask import Response, json, render_template, render_template_string
from langchain_google_genai import ChatGoogleGenerativeAI

from RAG_alpha_model import (
    init_argentic_model_params,
    load_documents,
    search_documentation,
)
from input_output_models import *


def load_html_files(directory: Path) -> Tuple[List[Path], List[str]]:
    html_file_names: List[str] = []
    html_file_paths: List[Path] = []

    for file in directory.iterdir():
        if file.is_file():
            if file.name.find(".html") != -1 and file.name.find("index") == -1:
                html_file_names.append(file.name)
                html_file_paths.append(file)

    print(f"Found {len(html_file_names)} '.html' files")
    return [html_file_paths, html_file_names]


from flask import Flask, request, send_from_directory

app = Flask(__name__)


@app.route("/assets/<path:filename>")
def assets(filename):
    return send_from_directory("templates/10/assets", filename)


@app.route("/v1/get_page")
def get_page():
    index = int(request.args.get("id"))
    return render_template(str(file_paths[index]))


@app.route("/v1/status")
def status():
    return [200, "ok"]


@app.route("/")
def home():
    return render_template("index.html")


from langchain.messages import HumanMessage


def parse_request(json_data: dict) -> Tuple[LLMEndpointInputV1, List[ErrorV1]]:
    request_errors: List[ErrorV1] = []
    parsed_request = None

    response_language = Language.validate(json_data.get("response_language", "pl"))

    prompt_context = json_data.get("prompt_context", [])

    prompt = json_data.get("prompt", None)
    user_id = json_data.get("user_id", None)
    conversation_id = json_data.get("conversation_id", None)

    if prompt is None:
        request_errors.append(ErrorV1(400, "Missing required 'prompt' param"))
    else:
        if type(prompt) is not str:
            request_errors.append(
                ErrorV1(
                    400,
                    f"Invalid 'prompt' param, expected string, received: {type(prompt)}",
                )
            )

    if user_id is None:
        request_errors.append(ErrorV1(400, "Missing required 'user_id' param"))
    else:
        if type(user_id) is not str:
            request_errors.append(
                ErrorV1(
                    400,
                    f"Invalid 'user_id' param, expected string, received: {type(user_id)}",
                )
            )
    if conversation_id is None:
        request_errors.append(ErrorV1(400, "Missing required 'conversation_id' param"))
    else:
        if type(conversation_id) is not str:
            request_errors.append(
                ErrorV1(
                    400,
                    f"Invalid 'conversation_id' param, expected string, received: {type(conversation_id)}",
                )
            )

    if len(request_errors) == 0:
        parsed_request = LLMEndpointInputV1(
            response_language, prompt_context, prompt, user_id, conversation_id
        )
    return [parsed_request, request_errors]


@app.route("/v1/prompt", methods=["POST"])
def assistant_prompt():
    data: LLMEndpointInputV1 | List[ErrorV1]
    data, errors = parse_request(request.get_json())

    if len(errors) != 0:
        return LLMEndpointErrorOutputV1.from_error_list(errors).to_flask_resp()

    markdown_response = ""
    tokens_used = 0
    try:

        markdown_response = "No response returned"

        print("generating response")
        response = agent.invoke({"messages": [HumanMessage(content=data.prompt)]})
        print("AI is done")

        for msg in response.get("messages", []):
            if msg.text:
                markdown_response += msg.text

        tokens_used = 22

    except Exception as e:
        # TODO parse model errors correctly
        print(e)
        return LLMEndpointErrorOutputV1.from_error_list(
            [ErrorV1(500, "Unexpected Server error")]
        ).to_flask_resp()

    return LLMEndpointOutputV1(
        response_language=data.response_language.value,
        prompt=data.prompt,
        user_id=data.user_id,
        conversation_id=data.conversation_id,
        tokens_used=tokens_used,
        markdown_response=markdown_response,
        files_utilized=[],
        models_used={
            "embedding": "models/gemini-embedding-001",
            "chat_model": "google_genai:gemini-3.6-flash",
        },
        http_status_code=200,
        tk_tokens_used=tokens_used,
    ).to_flask_resp()


@app.route("/v1/assistant_prompt", methods=["POST"])
def prompt():
    data: LLMEndpointInputV1 | List[ErrorV1]
    data, errors = parse_request(request.get_json())

    if len(errors) != 0:
        return LLMEndpointErrorOutputV1.from_error_list(errors).to_flask_resp()

    markdown_response = ""
    tokens_used = 0
    try:

        response = llm.invoke(data.prompt)
        print(f"input_tokens: {response.usage_metadata['input_tokens']}")
        print(f"output_tokens: {response.usage_metadata['output_tokens']}")
        tokens_used = response.usage_metadata["total_tokens"]
        print(f"resp: {response.content}")
        for msg in response.content:
            markdown_response += msg["text"]

    except Exception as e:
        # TODO parse model errors correctly
        print(e)
        return LLMEndpointErrorOutputV1.from_error_list(
            [ErrorV1(500, "Unexpected Server error")]
        ).to_flask_resp()

    return LLMEndpointOutputV1(
        response_language=data.response_language.value,
        prompt=data.prompt,
        user_id=data.user_id,
        conversation_id=data.conversation_id,
        tk_tokens_used=tokens_used,
        markdown_response=markdown_response,
        files_utilized=[],
        models_used={
            "chat_model": "google_genai:gemini-3.6-flash",
        },
        http_status_code=200,
    ).to_flask_resp()


def get_parser():
    parser = argparse.ArgumentParser(
        prog="In5 export server",
        description="Server providing html files exported by paid extension to InDesign: In5. Assumes directory organized with 'parse_in5_html.",
        usage="Provide required parameter, Source [-s] directory.",
    )

    parser.add_argument(
        "-s",
        "--source_directory",
        required=True,
        help="Directory where In5 deposited exported files.",
    )
    return parser


if __name__ == "__main__":
    parser = get_parser()
    args = parser.parse_args()

    print("Indexing .html files in directory args.source_directory")

    global file_paths
    global file_names
    file_paths, file_names = load_html_files(Path(args.source_directory))

    print("gemini-3.6-flash assistant model init")
    llm = ChatGoogleGenerativeAI(model="gemini-3.6-flash")

    print("Loading AI embeddings of loaded content")
    global agent
    agent = init_argentic_model_params(file_paths)

    app.run(host="0.0.0.0", port=8000, debug=True)
