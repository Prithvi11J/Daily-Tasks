import csv
import re
from pathlib import Path

from pypdf import PdfReader

# Find the project folders relative to this script.
PROJECT_DIR = Path(__file__).resolve().parent
PDF_DIR = PROJECT_DIR / "data" / "pdfs"
OUTPUT_CSV = PROJECT_DIR / "data" / "pdf_links.csv"

# Match URLs written visibly in the PDF text.
URL_PATTERN = re.compile(r"https?://[^\s<>\"']+|www\.[^\s<>\"']+")

# Keep track of which page each URL came from and how it was found.
found_links = {}


def add_link(pdf_name, page_number, url, found_by):
    """Save a URL and merge its discovery methods if it appears twice."""
    url = url.strip().rstrip(".,;:!?)]}")

    if not url:
        return

    key = (pdf_name, page_number, url)
    found_links.setdefault(key, set()).add(found_by)


def get_pdf_object(value):
    """Dereference a PDF object when pypdf provides an indirect reference."""
    if hasattr(value, "get_object"):
        return value.get_object()
    return value


# Read every PDF in data/pdfs.
pdf_files = sorted(PDF_DIR.glob("*.pdf"))

if not pdf_files:
    print(f"No PDF files found in: {PDF_DIR}")
else:
    for pdf_path in pdf_files:
        print(f"Scanning: {pdf_path.name}")

        try:
            reader = PdfReader(str(pdf_path))

            # Check every page for visible URLs and clickable links.
            for page_number, page in enumerate(reader.pages, start=1):
                # Find URLs printed as text on the page.
                page_text = page.extract_text() or ""
                for match in URL_PATTERN.findall(page_text):
                    add_link(pdf_path.name, page_number, match, "visible text")

                # Find URLs stored as clickable PDF links.
                annotations = page.get("/Annots") or []
                for annotation_ref in annotations:
                    annotation = get_pdf_object(annotation_ref)

                    if annotation.get("/Subtype") != "/Link":
                        continue

                    action = annotation.get("/A")
                    if not action:
                        continue

                    action = get_pdf_object(action)
                    url = action.get("/URI")

                    if url:
                        add_link(pdf_path.name, page_number, str(url), "clickable link")

        except Exception as error:
            print(f"Could not scan {pdf_path.name}: {error}")

    # Write the results into a CSV file you can open in Excel.
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_CSV.open("w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["pdf_file", "page", "url", "found_by"])

        for (pdf_name, page_number, url), methods in sorted(found_links.items()):
            writer.writerow([
                pdf_name,
                page_number,
                url,
                ", ".join(sorted(methods)),
            ])

    print(f"\nFound {len(found_links)} URL entries.")
    print(f"URL list saved to: {OUTPUT_CSV}")