from tkinter import messagebox
import fitz  # PyMuPDF
import pytesseract
from config import set_tesseract_path
from PIL import Image
import io

class OCRProcessor:
    def __init__(self, master):
        self.master = master

    @staticmethod
    def extract_text_from_pdf(pdf_path):
        try:
            set_tesseract_path()  # Call the function from config.py
        except FileNotFoundError as e:
            messagebox.showerror("Tesseract Error", str(e))
            return

        extracted_text = ""

        try:
            pdf_document = fitz.open(pdf_path)
        except Exception as e:
            return f"Error opening PDF: {e}"

        for page_num in range(len(pdf_document)):
            try:
                page = pdf_document.load_page(page_num)
                text = page.get_text("text")

                # If no extractable text, perform OCR
                if not text.strip():
                    # pix = page.get_pixmap()
                    # img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    # img = img.convert("L")  # Convert to grayscale for better OCR
                    pix = page.get_pixmap()
                    img = Image.open(io.BytesIO(pix.tobytes()))
                    img = img.convert("L")  # Convert to grayscale for better OCR
                    text = pytesseract.image_to_string(img)

                extracted_text += text + "\n"
            except Exception as e:
                extracted_text += f"\nError processing page {page_num}: {e}\n"

        return extracted_text
