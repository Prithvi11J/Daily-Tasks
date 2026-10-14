from pathlib import Path
from pypdf import PdfReader

# Find all PDFs in the project's PDF folder.
pdf_folder = Path(__file__).resolve().parent / "data" / "pdfs"
pdf_files = sorted(pdf_folder.glob("*.pdf"))

if not pdf_files:
    print(f"No PDFs found in: {pdf_folder}")
else:
    for pdf_file in pdf_files:
        print(f"\nPDF: {pdf_file.name}")

        try:
            reader = PdfReader(str(pdf_file))
            pages_with_little_text = []
            total_characters = 0
            sample_text = ""

            # Check how much text pypdf can read from each page.
            for page_number, page in enumerate(reader.pages, start=1):
                text = page.extract_text() or ""
                character_count = len(text.strip())
                total_characters += character_count

                if character_count < 30:
                    pages_with_little_text.append(page_number)

                if not sample_text and character_count >= 30:
                    sample_text = " ".join(text.split())[:200]

            print(f"Pages: {len(reader.pages)}")
            print(f"Extracted characters: {total_characters}")
            print(f"Pages with little or no text: {len(pages_with_little_text)}")

            if pages_with_little_text:
                print(f"Example page numbers: {pages_with_little_text[:10]}")

            print(f"Text sample: {sample_text or '[No readable text found]'}")

        except Exception as error:
            print(f"Could not read this PDF: {error}")