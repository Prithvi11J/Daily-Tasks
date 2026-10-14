import os
import re
from pathlib import Path

import pymupdf
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


# All paths are relative to this script's folder.
PROJECT_DIR = Path(__file__).resolve().parent
PDF_DIR = PROJECT_DIR / "data" / "pdfs"
WEB_DIR = PROJECT_DIR / "data" / "web_sources"
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
INDEX_DIR = PROJECT_DIR / "data" / "faiss_index"

RAW_OCR_FILE = PROCESSED_DIR / "micro_irrigation_full_ocr_raw.txt"

# These pages looked more readable in the OCR preview.
# The table-heavy and garbled pages are left out to avoid bad figures.
OCR_PAGES_TO_INDEX = {3, 8, 11, 12, 13, 14}

MIN_PDF_PAGE_CHARACTERS = 80
MIN_OCR_PAGE_CHARACTERS = 150
MIN_OCR_ENGLISH_WORDS = 12

VERIFIED_TRANSCRIPT_FILES = [
    PROCESSED_DIR / "micro_irrigation_verified_page_1.txt",
    PROCESSED_DIR / "micro_irrigation_verified_page_2.txt",
]


def load_readable_pdf_pages():
    """Load selectable text from pages in all PDFs."""
    documents = []

    if not PDF_DIR.exists():
        print(f"PDF folder not found: {PDF_DIR}")
        return documents

    for pdf_path in sorted(PDF_DIR.glob("*.pdf")):
        readable_page_count = 0

        try:
            with pymupdf.open(pdf_path) as pdf:
                for page_number, page in enumerate(pdf, start=1):
                    text = page.get_text("text").strip()

                    if len(text) < MIN_PDF_PAGE_CHARACTERS:
                        continue

                    documents.append(
                        Document(
                            page_content=text,
                            metadata={
                                "source": pdf_path.name,
                                "page": page_number,
                                "source_type": "pdf",
                            },
                        )
                    )
                    readable_page_count += 1

            print(
                f"Loaded {readable_page_count} readable pages "
                f"from {pdf_path.name}"
            )

            if readable_page_count == 0:
                print(
                    "  This PDF appears to be scanned; verified transcripts "
                    "and selected OCR pages are handled separately."
                )

        except Exception as error:
            print(f"Could not read {pdf_path.name}: {error}")

    return documents


def load_saved_web_pages():
    """Load saved website text files; this does not fetch live web pages."""
    documents = []

    if not WEB_DIR.exists():
        print(f"Website text folder not found: {WEB_DIR}")
        return documents

    for text_path in sorted(WEB_DIR.glob("*.txt")):
        if text_path.name.lower() == "urls.txt":
            continue

        try:
            text = text_path.read_text(
                encoding="utf-8",
                errors="replace",
            ).strip()

            if not text:
                continue

            url_match = re.search(
                r"^[ \t]*Source URL:[ \t]*(\S+)",
                text,
                flags=re.IGNORECASE | re.MULTILINE,
            )

            metadata = {
                "source": text_path.name,
                "source_type": "saved_website",
            }

            if url_match:
                metadata["url"] = url_match.group(1)

            documents.append(
                Document(
                    page_content=text,
                    metadata=metadata,
                )
            )
            print(f"Loaded saved website text from {text_path.name}")

        except Exception as error:
            print(f"Could not read {text_path.name}: {error}")

    return documents


def load_verified_transcriptions():
    """Load the manually checked text for scanned pages 1 and 2."""
    documents = []

    for transcript_path in VERIFIED_TRANSCRIPT_FILES:
        if not transcript_path.exists():
            print(f"Verified transcript not found, skipping: {transcript_path.name}")
            continue

        try:
            text = transcript_path.read_text(
                encoding="utf-8",
                errors="replace",
            ).strip()

            if not text:
                print(f"Verified transcript is empty, skipping: {transcript_path.name}")
                continue

            source_match = re.search(
                r"^[ \t]*Source PDF:[ \t]*(.+)$",
                text,
                flags=re.IGNORECASE | re.MULTILINE,
            )
            page_match = re.search(
                r"^[ \t]*Page:[ \t]*(\d+)[ \t]*$",
                text,
                flags=re.IGNORECASE | re.MULTILINE,
            )

            source_name = (
                source_match.group(1).strip()
                if source_match
                else "2026-27-Micro-Irrigation-First-Instalment-GO-(87).pdf"
            )

            if not page_match:
                print(
                    f"No page number found in {transcript_path.name}; "
                    "skipping it so citations stay accurate."
                )
                continue

            page_number = int(page_match.group(1))

            documents.append(
                Document(
                    page_content=text,
                    metadata={
                        "source": source_name,
                        "page": page_number,
                        "source_type": "verified_transcription",
                    },
                )
            )
            print(
                f"Loaded verified transcription for "
                f"{source_name}, page {page_number}"
            )

        except Exception as error:
            print(f"Could not read {transcript_path.name}: {error}")

    return documents


def load_selected_ocr_pages():
    """Load selected OCR pages that pass basic readability checks."""
    documents = []

    if not RAW_OCR_FILE.exists():
        print(f"Raw OCR file not found, skipping: {RAW_OCR_FILE}")
        return documents

    try:
        raw_text = RAW_OCR_FILE.read_text(
            encoding="utf-8",
            errors="replace",
        )
    except Exception as error:
        print(f"Could not read the raw OCR file: {error}")
        return documents

    page_heading_pattern = re.compile(
        r"^[ \t]*--- Page (\d+) ---[ \t]*$",
        flags=re.MULTILINE,
    )
    headings = list(page_heading_pattern.finditer(raw_text))

    if not headings:
        print("No page headings found in the raw OCR file.")
        return documents

    for index, heading in enumerate(headings):
        page_number = int(heading.group(1))

        if page_number not in OCR_PAGES_TO_INDEX:
            continue

        page_start = heading.end()
        page_end = (
            headings[index + 1].start()
            if index + 1 < len(headings)
            else len(raw_text)
        )
        page_text = raw_text[page_start:page_end].strip()

        page_text = re.sub(
            r"^[ \t]*\[No text recognized\][ \t]*$",
            "",
            page_text,
            flags=re.IGNORECASE | re.MULTILINE,
        ).strip()

        english_words = re.findall(r"\b[A-Za-z]{3,}\b", page_text)

        if len(page_text) < MIN_OCR_PAGE_CHARACTERS:
            print(f"Skipped OCR page {page_number}: too little text.")
            continue

        if len(english_words) < MIN_OCR_ENGLISH_WORDS:
            print(f"Skipped OCR page {page_number}: OCR text looks unclear.")
            continue

        source_name = "2026-27-Micro-Irrigation-First-Instalment-GO-(87).pdf"

        documents.append(
            Document(
                page_content=page_text,
                metadata={
                    "source": source_name,
                    "page": page_number,
                    "source_type": "ocr",
                },
            )
        )
        print(f"Loaded readable OCR text for {source_name}, page {page_number}")

    return documents


def main():
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit(
            "OPENAI_API_KEY was not found. Set it in this terminal, "
            "then run this script again."
        )

    documents = []
    documents.extend(load_readable_pdf_pages())
    documents.extend(load_saved_web_pages())
    documents.extend(load_verified_transcriptions())
    documents.extend(load_selected_ocr_pages())

    if not documents:
        raise SystemExit("No source documents were found to index.")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200,
        chunk_overlap=200,
        add_start_index=True,
    )
    chunks = splitter.split_documents(documents)

    if not chunks:
        raise SystemExit("No text chunks were created for the FAISS index.")

    print(f"\nPrepared {len(chunks)} text chunks for indexing.")

    # Embedding the selected text uses the OpenAI API.
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vector_store = FAISS.from_documents(chunks, embeddings)

    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    vector_store.save_local(str(INDEX_DIR))

    print(f"\nFAISS index saved to: {INDEX_DIR}")
    print(
        f"Indexed {len(documents)} source documents/pages "
        f"into {len(chunks)} chunks."
    )


if __name__ == "__main__":
    main()