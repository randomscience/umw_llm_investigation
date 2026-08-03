import argparse
from pathlib import Path
from typing import List, Tuple
from flask import Response, render_template, render_template_string


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


@app.route("/")
def home():
    urls = []
    for i in range(len(file_names)):
        urls.append({"name": file_names[i], "url": f"/v1/get_page?id={i}"})

    return render_template("index.html", links=urls)


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

    print(f"Indexing .html files in directory args.source_directory")

    global file_paths
    global file_names
    file_paths, file_names = load_html_files(Path(args.source_directory))

    app.run(host="0.0.0.0", port=8000, debug=True)
