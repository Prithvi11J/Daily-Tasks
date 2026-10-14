from pathlib import Path
import pymupdf

# Locate the project, source PDF, Tesseract language files, and output file.
PROJECT_FOLDER = Path(__file__).resolve().parent

PDF_PATH = (
    PROJECT_FOLDER
    / "data"
    / "pdfs"
    / "2026-27-Micro-Irrigation-First-Instalment-GO-(87).pdf"
)

TESSDATA_FOLDER = Path(r"C:\Program Files\Tesseract-OCR\tessdata")

OUTPUT_PATH = (
    PROJECT_FOLDER
    / "data"
    / "processed"
    / "micro_irrigation_full_ocr_raw.txt"
)

# Stop with a clear message if a required file or folder is missing.
if not PDF_PATH.exists():
    raise FileNotFoundError(f"Could not find the PDF: {PDF_PATH}")

if not TESSDATA_FOLDER.exists():
    raise FileNotFoundError(
        f"Could not find Tesseract's language folder: {TESSDATA_FOLDER}"
    )

# Use Tamil OCR too if its language model is installed.
tamil_model = TESSDATA_FOLDER / "tam.traineddata"
languages = "eng+tam" if tamil_model.exists() else "eng"
print(f"Using OCR languages: {languages}")

# Open the PDF and prepare the output folder.
document = pymupdf.open(PDF_PATH)
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

# Open the output file ONCE before the loop so each page is added to it.
with OUTPUT_PATH.open("w", encoding="utf-8") as output_file:
    output_file.write(f"Source PDF: {PDF_PATH.name}\n")
    output_file.write(f"OCR languages: {languages}\n")

    # OCR each page and append its text to the same output file.
    for page_index in range(len(document)):
        page_number = page_index + 1
        page = document[page_index]

        print(f"Reading page {page_number} of {len(document)}...")

        ocr_text_page = page.get_textpage_ocr(
            language=languages,
            dpi=400,
            full=True,
            tessdata=str(TESSDATA_FOLDER),
        )

        extracted_text = page.get_text("text", textpage=ocr_text_page).strip()

        output_file.write(f"\n--- Page {page_number} ---\n")
        output_file.write(extracted_text or "[No text recognized]")
        output_file.write("\n")

document.close()
print(f"\nOCR text saved to: {OUTPUT_PATH}")