import os
from typing import List, Tuple

import shutil
import argparse
from pathlib import Path

from bs4 import BeautifulSoup


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


def parse_in5_html_file(file_path: Path, target_path: Path):

    with open(file_path, "r", encoding="utf-8") as f:
        html = f.read()
    
    html = html.replace("﻿", "")
    
    soup = BeautifulSoup(html, "html.parser")

    elems_to_remove = ["page-nav", "in5footer", "prefooter", "loadIndicator"]

    for i in elems_to_remove:
        element = soup.find(id=i)
        if element:
            element.decompose()

    for script in soup.find_all("script"):
        script.decompose()

    if not target_path.exists():
        target_path.parent.mkdir(parents=True, exist_ok=True)

    with open(target_path, "w", encoding="utf-8") as f:
        f.write(str(soup))


def get_parser():
    parser = argparse.ArgumentParser(
        prog="In5 result parser",
        description="Parser for html files exported by paid extension to InDesign: In5.",
        usage="Provide two required parameters, Source [-s] and Destination [-d] directories: python .\parse_in5_html.py -s .\templates\10 -d .\templates\res",
    )

    parser.add_argument(
        "-s",
        "--source_directory",
        required=True,
        help="Directory where In5 deposited exported files.",
    )
    parser.add_argument(
        "-d",
        "--destination_directory",
        required=True,
        help="Destination directory where result will be deposited.",
    )
    parser.add_argument(
        "-a",
        "--assets_directory_name",
        required=False,
        help="Name of directory containing assets for html files, by default it's 'assets'.",
        default="assets",
    )
    return parser


if __name__ == "__main__":
    parser = get_parser()
    args = parser.parse_args()

    file_paths, file_names = load_html_files(Path(args.source_directory))

    for file in zip(file_paths, file_names):
        target_path = Path(args.destination_directory, file[1])
        parse_in5_html_file(file[0], target_path)

    print(f"Saved {len(file_paths)} to directory {args.destination_directory}")

    print(f"Copying assets file")

    shutil.copytree(
        Path(args.source_directory, args.assets_directory_name),
        Path(args.destination_directory, args.assets_directory_name),
        dirs_exist_ok=True,
    )
