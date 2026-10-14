from datetime import datetime
from pathlib import Path
import re
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

# Locate the URL list and the folder where scraped text will be saved.
PROJECT_DIR = Path(__file__).resolve().parent
WEB_SOURCES_DIR = PROJECT_DIR / "data" / "web_sources"
URLS_FILE = WEB_SOURCES_DIR / "urls.txt"

# Read the URLs, ignoring blank lines and comments.
urls = [
    line.strip()
    for line in URLS_FILE.read_text(encoding="utf-8").splitlines()
    if line.strip() and not line.strip().startswith("#")
]

# Fetch each page and save its readable text with source details.
for url in dict.fromkeys(urls):  # Avoid fetching the same URL twice.
    try:
        response = requests.get(
            url,
            timeout=30,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        response.raise_for_status()

        # This script handles web pages, not PDF files.
        content_type = response.headers.get("Content-Type", "").lower()
        if "html" not in content_type:
            print(f"Skipped (not an HTML page): {url}")
            continue

        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.title.get_text(" ", strip=True) if soup.title else "Untitled page"

        # Remove page elements that are usually menus or code, not article text.
        for tag in soup(["script", "style", "noscript", "svg", "nav", "footer"]):
            tag.decompose()

        page_text = soup.get_text(separator="\n", strip=True)
        page_text = "\n".join(
            line.strip() for line in page_text.splitlines() if line.strip()
        )

        # Make a safe filename based on the website address.
        parsed_url = urlparse(url)
        name_parts = parsed_url.netloc + "_" + parsed_url.path.strip("/")
        filename = re.sub(r"[^a-zA-Z0-9]+", "_", name_parts).strip("_").lower()
        if not parsed_url.path.strip("/"):
            filename += "_home"

        output_file = WEB_SOURCES_DIR / f"{filename}.txt"

        # Keep the original URL and retrieval time for source tracking.
        saved_text = (
            f"Source URL: {url}\n"
            f"Page title: {title}\n"
            f"Retrieved: {datetime.now().isoformat(timespec='minutes')}\n\n"
            f"{page_text}\n"
        )
        output_file.write_text(saved_text, encoding="utf-8")

        print(f"Saved: {output_file.name}")

    except requests.RequestException as error:
        print(f"Could not fetch {url}: {error}")