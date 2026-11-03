import re
import unicodedata
from pathlib import Path

DATA_DIR = Path("data")
INPUT_DIR = DATA_DIR / "processed"
OUTPUT_DIR = DATA_DIR / "processed"

def preprocess_text(text):
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\x00", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[•▪◦]", "\n", text)

    return text.strip()


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for file_path in INPUT_DIR.glob("*.txt"):
        text = file_path.read_text(encoding="utf-8")
        processed = preprocess_text(text)
        output_path = OUTPUT_DIR / f"{file_path.stem}-processed.txt"
        output_path.write_text(
            processed,
            encoding="utf-8"
        )

        print(f"Processed: {file_path.name}")

if __name__ == "__main__":
    main()