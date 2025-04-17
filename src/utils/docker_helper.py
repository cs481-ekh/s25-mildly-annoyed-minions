import os

from src.ocr import OCRProcessorNoGUI as OCRProcessor


def main():
    if os.path.exists("/app/input"):
        processor = OCRProcessor()
        for file in os.listdir("/app/input"):
            text = processor.extract_text_from_pdf(f"/app/input/{file}")
            print(text)
            processor.save_csv(f"/app/output/{file.replace(".pdf", ".csv")}", text[1])
    else:
        print(f"{os.getenv("INPUT_FILES_DIR")} not found")
        exit(1)

if __name__ == "__main__":
    main()
