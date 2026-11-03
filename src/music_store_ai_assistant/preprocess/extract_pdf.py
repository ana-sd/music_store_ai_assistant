import pymupdf
from pathlib import Path

DATA_DIR = Path("data")
INPUT_DIR = DATA_DIR / "raw"
OUTPUT_DIR = DATA_DIR / "processed"

def extract_pdf(pdf_path):
    pages = []

    with pymupdf.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf, start=1):
            text = page.get_text("text").strip()
            if text:
                pages.append({
                    "page": page_number,
                    "text": text
                })

    return pages


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for pdf_path in INPUT_DIR.glob("*.pdf"):
        pages = extract_pdf(pdf_path)
        output_path = OUTPUT_DIR / f"{pdf_path.stem}-extracted.txt"
        content = "\n\n".join(
            f"--- Page {page['page']} ---\n{page['text']}"
            for page in pages
        )
        output_path.write_text(content, encoding="utf-8")

        print(f"{pdf_path.name}: {len(pages)} pages extracted")

if __name__ == "__main__":
    main()