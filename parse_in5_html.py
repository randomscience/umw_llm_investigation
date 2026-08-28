from typing import List, Tuple
import argparse
from pathlib import Path


def load_html_files(directory: Path) -> Tuple[List[int], List[Path], List[str]]:
    html_file_names: List[str] = []
    html_file_paths: List[Path] = []
    html_file_chapter: List[int] = []

    for chapter in directory.iterdir():
        if chapter.is_dir():
            for file in chapter.iterdir():
                if file.is_file():
                    if file.name.find(".html") != -1 and file.name.find("index") == -1:
                        html_file_names.append(file.name)
                        html_file_paths.append(Path(file))
                        html_file_chapter.append(int(chapter.name))

    print(f"Found {len(html_file_names)} '.html' files")
    return [html_file_chapter, html_file_paths, html_file_names]


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

    return parser


if __name__ == "__main__":
    parser = get_parser()
    args = parser.parse_args()

    chapter, file_paths, file_names = load_html_files(Path(args.source_directory))

    print(f"Saved {len(file_paths)} to directory {args.destination_directory}")

    chapter, file_paths = zip(*sorted(zip(chapter, file_paths)))

    index = 9

    print("---------------")
    print(str(file_paths))
    for path in file_paths:
        with open(path, "r", encoding="utf-8") as f:

            html = f.read()
            with open(
                f"{args.destination_directory}\\{index}.html", "w", encoding="utf-8"
            ) as f2:
                f2.write(html)
                index += 1
