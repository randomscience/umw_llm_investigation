import os
from pathlib import Path

from bs4 import BeautifulSoup
from flask import Response

directory = Path("c:\\D\\UMWR_LLM_INVESTIGATION\\templates\\10")


def load_html_files():
    html_files = []
    for file in directory.iterdir():
        if file.is_file():
            if file.name.find(".html") != -1:
                print(file.name)
                # filter correct schema
                html_files.append(file.name)

    return html_files


html_files = load_html_files()


def parse_in5_html_file(path):

    with open(path, "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")

    elems_to_remove = ["page-nav", "in5footer", "prefooter", "loadIndicator"]

    for i in elems_to_remove:
        element = soup.find(id=i)
        if element:
            element.decompose()

    for script in soup.find_all("script"):
        script.decompose()

    return Response(str(soup), mimetype="text/html")


from flask import Flask, request, send_from_directory

app = Flask(__name__)


@app.route("/assets/<path:filename>")
def assets(filename):
    return send_from_directory("templates/10/assets", filename)


@app.route("/")
def home():
    index = int(request.args.get("id"))

    print(index)
    return parse_in5_html_file("templates/10/" + html_files[index])
    # return render_template("10/" + html_files[index])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
