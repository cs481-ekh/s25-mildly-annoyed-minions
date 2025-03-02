import os
import csv
from tkinter import messagebox
import fitz
import pytesseract
from config import set_tesseract_path
from PIL import Image
import io


class OCRProcessor:
    def __init__(self, master):
        self.master = master

    def extract_text_from_pdf(self, pdf_path):
        try:
            set_tesseract_path()  # Call the function from config.py
        except FileNotFoundError as e:
            self.master.gui.handle_error("Tesseract Error", str(e))
            return None, None

        extracted_text = ""
        csv_path = pdf_path.replace(".pdf", ".csv")  # Define CSV file path

        try:
            pdf_document = fitz.open(pdf_path)
        except Exception as e:
            # messagebox.showerror("Error", f"Error opening PDF: {e}")
            self.master.gui.handle_error("File Handling Error", "Error opening PDF file: str(e)")
            return None, None

        for page_num in range(len(pdf_document)):
            try:
                page = pdf_document.load_page(page_num)
                text = page.get_text("text")

                # If no extractable text, perform OCR
                if not text.strip():
                    pix = page.get_pixmap()
                    img = Image.open(io.BytesIO(pix.tobytes()))
                    img = img.convert("L")  # Convert to grayscale for better OCR
                    text = pytesseract.image_to_string(img)

                extracted_text += text + "\n"
            except Exception as e:
                extracted_text += f"\nError processing page {page_num}: {e}\n"

        return csv_path, extracted_text

    def save_csv(self, extracted_text, csv_path):
        try:
            with open(csv_path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(['Page Number', 'Extracted Text'])
                for page_num, text in enumerate(extracted_text.split('\n\n')):
                    writer.writerow([page_num + 1, text])
            return csv_path
        except Exception as e:
            self.master.gui.handle_error("File Save Error", f"Failed to save CSV file: {str(e)}")
            return None