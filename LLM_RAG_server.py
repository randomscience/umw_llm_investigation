import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple
from deepagents import create_deep_agent
from flask import Response, render_template, render_template_string

from RAG_alpha_model import INSTRUCTIONS, init_argentic_model_params, load_documents


from langchain.messages import HumanMessage
from flask import Flask, request, send_from_directory

app = Flask(__name__)

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



@app.route("/alpha_agent")
def get_agent_resp():
    query = str(request.args.get("query"))
    result = agent.invoke({"messages": [HumanMessage(content=query)]})

    for msg in result.get("messages", []):
        if msg.text:
            print(msg.text)

    return Response()



if __name__ == "__main__":
    parser = get_parser()
    args = parser.parse_args()

    print(f"Indexing .html files in directory args.source_directory")

    global agent
    agent = init_argentic_model_params(Path("./templates/res"))

    app.run(host="0.0.0.0", port=8000, debug=True)
