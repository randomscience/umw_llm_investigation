import os
import sys

import urllib.request
from pathlib import Path

from dotenv import load_dotenv
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

load_dotenv()


def main():
    url = os.environ.get("EMBEDDINGS_URL")
    if not url or url == "":
        logger.info("EMBEDDINGS_URL not set skipping download")
        return

    logger.info(f"Downloading embeddings from {url}")

    CACHE_FILE = Path(os.environ.get("CACHE_FILE", "embedding_cache.json"))
    urllib.request.urlretrieve(url, CACHE_FILE)
    logger.info(f"Embeddings downloaded and saved to {CACHE_FILE}")


if __name__ == "__main__":
    main()
