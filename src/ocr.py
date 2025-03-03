import os
import csv
from tkinter import messagebox
import pytesseract
from src.config import set_tesseract_path
from pdf2image import convert_from_path
from PIL import Image, ImageSequence


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

        image_path = self.convert_pdf_to_tiff(pdf_path)  # Get path to TIFF converted image
        if image_path is not None:
            with Image.open(image_path) as img:
                for page_num, frame in enumerate(ImageSequence.Iterator(img)):
                    try:
                        text = pytesseract.image_to_string(frame, lang='eng')

                        extracted_text += text + "\n"
                    except Exception as e:
                        extracted_text += f"\nError processing page {page_num + 1}: {e}\n"

                os.remove(image_path)  # Delete file once done with it

        return csv_path, extracted_text

    def convert_pdf_to_tiff(self, pdf_path):
        try:
            images = convert_from_path(
                pdf_path,
                grayscale=True,
                fmt='tiff',
            )

            tiff_path = pdf_path.replace(".pdf", ".tif")  # Define TIFF file path

            if len(images) != 0:
                images[0].save(tiff_path, save_all=True, append_images=images[1:])

                return tiff_path
            else:
                self.master.gui.handle_error("Error", f"Error converting PDF to TIFF: {pdf_path}")
                return None
        except Exception as e:
            self.master.gui.handle_error("File Handling Error", f"Unable to open file: {pdf_path}")
            return None

    def save_csv(self, csv_path, extracted_text):
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