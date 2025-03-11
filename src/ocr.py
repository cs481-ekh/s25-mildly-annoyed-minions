import os
import csv
import re
import pytesseract

from PIL import Image
from pdf2image import convert_from_path
from src.config import set_tesseract_path

class OCRProcessor:
    def __init__(self, master):
        self.master = master

    def extract_text_from_pdf(self, pdf_path):
        """
        1) Convert each PDF page into a PIL Image in memory.
        2) Run Tesseract OCR on each image.
        3) Extract the year from the PDF filename (first 4 digits).
        4) Pass text + extracted year to parse_extracted_text.
        5) Return (None, None) if something fails, or (csv_path, parsed_data) if success.
        """
        try:
            set_tesseract_path()  # Ensure Tesseract is configured
        except FileNotFoundError as e:
            self.master.gui.handle_error("Tesseract Error", str(e))
            return None

        # Extract the year from the filename (e.g. "1975-whatever.pdf")
        base_name = os.path.basename(pdf_path)
        match = re.match(r'^(\d{4})', base_name)
        year_from_file = match.group(1) if match else "Unknown"

        # Prepare a default CSV path
        filename_default = base_name.replace(".pdf", ".csv")
        csv_path_default = os.path.join(os.path.dirname(pdf_path), filename_default)

        # Convert PDF pages to PIL Images in memory
        try:
            images = convert_from_path(pdf_path, grayscale=True)
            if not images:
                self.master.gui.handle_error("Error", f"No pages found in PDF: {pdf_path}")
                return None
        except Exception as e:
            self.master.gui.handle_error(
                "File Handling Error",
                f"Unable to open file: {pdf_path}\n{e}"
            )
            return None

        # OCR each page Image
        extracted_text = ""
        for page_num, pil_image in enumerate(images, start=1):
            try:
                page_text = pytesseract.image_to_string(pil_image, lang='eng', config='--psm 6')
                # Remove lines starting with =- etc.
                page_text = re.sub(r'(?m)^[-=]+\s*', '', page_text)
                extracted_text += page_text + "\n"
            except Exception as e:
                extracted_text += f"\nError processing page {page_num}: {e}\n"

        # Parse the text
        parsed_data = self.parse_extracted_text(extracted_text, year_from_file)
        return csv_path_default, parsed_data

    def parse_extracted_text(self, text, year):
        """
        Uses a block-based approach to parse out:
          code, title, street, city, state, zip, phone, etc.
        """
        lines = text.splitlines()

        # If OCR mistakes occur, map them to correct code
        code_map = {
            "Al": "A1",
            "aA": "A1.1",
            "2":  "A1.2",
            # etc...
        }

        data = []
        current_code = None
        current_title = ""
        current_block_lines = []

        def save_block(code, title, block_lines):
            if not code:
                return None

            # Fix common misreads
            if code in code_map:
                code = code_map[code]

            block_text = " ".join(block_lines)

            # P.O. Box
            street_match = re.search(r'(P\.?\s?O\.?\s?Box\s?\d+)', block_text, re.IGNORECASE)
            street = street_match.group(1) if street_match else ""

            # City, State, Zip
            csz_match = re.search(r'([A-Za-z]+),\s*([A-Z]{2})\s+(\d{5})', block_text)
            if csz_match:
                city, state, zipcode = csz_match.groups()
            else:
                city, state, zipcode = "", "", ""

            # Phone (FIXED REGEX)
            phone_match = re.search(r'(\(?\d{3}\)?[\s-]?\d{3}-\d{4})', block_text)
            phone = phone_match.group(1) if phone_match else ""

            # Tag (pf)
            tag = 'pf' if '(pf)' in block_text else ""

            # Professional staff
            staff_match = re.search(r'Professional\s+staff\s+(\d+)', block_text, re.IGNORECASE)
            staff = staff_match.group(1) if staff_match else ""

            # Technicians
            techs_match = re.search(r'(\d+)\s+technicians', block_text, re.IGNORECASE)
            num_techs = techs_match.group(1) if techs_match else ""

            # Fields
            fields_match = re.search(r'Field of R&D:\s*(.*)', block_text, re.IGNORECASE)
            fields = fields_match.group(1) if fields_match else ""

            return {
                'year': year,
                'code': code,
                'title': title,
                'street': street,
                'city': city,
                'state': state,
                'zip': zipcode,
                'phone': phone,
                'tag': tag,
                'staff': staff,
                'doctorates': "",
                'numTechsAndAuxs': num_techs,
                'fields': fields,
                'note': ""
            }

        # Iterate over lines; if it starts with code, treat as new block
        for line in lines:
            ln = line.strip()
            if not ln:
                continue

            tokens = ln.split(maxsplit=1)
            if not tokens:
                continue

            first_token = tokens[0]

            # If recognized as a code (like "A1", "Al", etc.),
            # that starts a new block
            if first_token in code_map or re.match(r'^[A-Za-z]\d+', first_token):
                # Save previous block
                if current_code:
                    block_data = save_block(current_code, current_title, current_block_lines)
                    if block_data:
                        data.append(block_data)

                current_code = first_token
                current_title = tokens[1].strip() if len(tokens) > 1 else ""
                current_block_lines = []
            else:
                # Accumulate lines in current block
                if current_code:
                    current_block_lines.append(ln)

        # Final block
        if current_code:
            block_data = save_block(current_code, current_title, current_block_lines)
            if block_data:
                data.append(block_data)

        return data

    def save_csv(self, csv_path, parsed_data):
        """
        Prompt the user for a file name & location and save CSV.
        """
        from tkinter import filedialog

        chosen_path = filedialog.asksaveasfilename(
            title="Save CSV As",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not chosen_path:
            self.master.gui.handle_error("Save Error", "No file was selected.")
            return None

        try:
            with open(chosen_path, mode='w', newline='', encoding='utf-8') as file:
                fieldnames = [
                    'year', 'code', 'title', 'street', 'city', 'state', 'zip', 'phone',
                    'tag', 'staff', 'doctorates', 'numTechsAndAuxs', 'fields', 'note'
                ]
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(parsed_data)

            self.master.gui.show_info("File Saved", f"CSV file saved to:\n{chosen_path}")
            return chosen_path

        except Exception as e:
            error_message = f"Failed to save CSV file: {str(e)}"
            self.master.gui.handle_error("File Save Error", error_message)
            return None
