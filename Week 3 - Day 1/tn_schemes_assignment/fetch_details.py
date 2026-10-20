"""Fetch detailed scheme pages listed in data/schemes.json.
Run: python fetch_details.py
This is optional; the chatbot works with the 54 listing records without it.
"""
import json
import time
from pathlib import Path
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

FILE = Path(__file__).parent / "data" / "schemes.json"

def fetch_description(session, url):
    response = session.get(url, timeout=18)
    response.raise_for_status()
    final = urlparse(response.url)
    if final.hostname not in {"www.tn.gov.in", "tn.gov.in"}:
        raise ValueError("Unexpected redirect outside tn.gov.in")
    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "form"]):
        tag.decompose()
    # The page template may differ by scheme. Prefer its content region.
    candidates = [soup.select_one(sel) for sel in (
        "div.dept_inner_container", "div.scheme-details", "article", "main", "div.container")]
    region = next((x for x in candidates if x and len(x.get_text(" ",strip=True)) > 100), soup.body)
    text = "\n".join(dict.fromkeys(
        " ".join(tag.stripped_strings) for tag in region.select("p, li, tr, h1, h2, h3, h4")
        if 12 < len(" ".join(tag.stripped_strings)) < 2500
    ))
    if not text or len(text)<45:
        raise ValueError("Detailed content not found")
    return text[:30000]

def main():
    records=json.loads(FILE.read_text(encoding="utf-8"))
    session=requests.Session()
    session.headers.update({"User-Agent":"Mozilla/5.0 (Educational scheme information research)"})
    passed=0
    failed=0
    for i, scheme in enumerate(records,1):
        if scheme.get("status")=="detail_fetched" and scheme.get("description"):
            passed+=1
            continue
        try:
            scheme["description"]=fetch_description(session,scheme["url"])
            scheme["status"]="detail_fetched"
            passed+=1
            print(f"[{i}/{len(records)}] OK: {scheme['name']}")
        except (requests.RequestException,ValueError) as ex:
            scheme["status"]="listing_only"
            failed+=1
            print(f"[{i}/{len(records)}] Not fetched ({type(ex).__name__}): {scheme['name']}")
        FILE.write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding="utf-8")
        time.sleep(1)
    print(f"Done: {passed} details available; {failed} unavailable. Total schemes: {len(records)}")
if __name__=="__main__":
    main()
