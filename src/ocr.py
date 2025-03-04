import os
import csv
import re
import pytesseract

from PIL import Image, ImageSequence
from src.config import set_tesseract_path

class OCRProcessor:
    def __init__(self, master):
        self.master = master

    def extract_text_from_pdf(self, pdf_path):
        """
        1) Convert the PDF to TIFF and run Tesseract to get OCR text.
        2) Extract the year from the PDF filename (first 4 digits).
        3) Pass text + extracted year to parse_extracted_text.
        4) Return (None, None) if something fails, or (csv_path, parsed_data) if success.
        """
        try:
            set_tesseract_path()  # Call the function from config.py
        except FileNotFoundError as e:
            self.master.gui.handle_error("Tesseract Error", str(e))
            return None

        # Extract the year from the first 4 digits of the PDF filename
        base_name = os.path.basename(pdf_path)  # e.g. "1975-a1_1-2.pdf"
        match = re.match(r'^(\d{4})', base_name)
        if match:
            year_from_file = match.group(1)
        else:
            year_from_file = "Unknown"  # fallback if no 4-digit prefix

        extracted_text = ""
        # We'll still create a default CSV path, but won't automatically use it for saving
        filename_default = base_name.replace(".pdf", ".csv")
        csv_path_default = os.path.join(os.path.dirname(pdf_path), filename_default)

        image_path = self.convert_pdf_to_tiff(pdf_path)
        if image_path is not None:
            try:
                with Image.open(image_path) as img:
                    for page_num, frame in enumerate(ImageSequence.Iterator(img)):
                        try:
                            text = pytesseract.image_to_string(
                                frame, lang='eng', config='--psm 6'
                            )
                            extracted_text += text + "\n"
                        except Exception as e:
                            extracted_text += f"\nError processing page {page_num + 1}: {e}\n"
            finally:
                # Optionally remove the TIFF
                if os.path.exists(image_path):
                    # your existing removal logic or partial removal
                    pass

        # Now parse the text, passing the year
        parsed_data = self.parse_extracted_text(extracted_text, year_from_file)
        return csv_path_default, parsed_data

    def parse_extracted_text(self, text, year):
        """
        Example parse logic that uses the 'year' extracted from the PDF filename
        (instead of hardcoding '1975').
        """

        lines = text.splitlines()
        data = []

        # For demonstration, let's do a very simple approach that captures
        # top-level code lines in the form 'Al AAI CORPORATION' => code='Al', title='AAI CORPORATION'
        # Then we have a dictionary to fix codes:
        code_map = {
            "Al": "A1",
            "aA": "A1.1",
            "2":  "A1.2",
        }

        current_code = None
        current_title = ""
        current_block_lines = []

        def save_block(code, title, block):
            if not code:
                return None

            # block_text used for the phone, staff, etc.
            block_text = " ".join(block)

            # Quick example regexes:
            street_match = re.search(r'(P\.?\s?O\.?\s?Box\s?\d+)', block_text, re.IGNORECASE)
            street = street_match.group(0) if street_match else ""

            csz_match = re.search(r'([A-Za-z]+),\s*([A-Z]{2})\s+(\d{5})', block_text)
            if csz_match:
                city, state, zipcode = csz_match.groups()
            else:
                city, state, zipcode = "", "", ""

            phone_match = re.search(r'(\(?\d{3}\)?[\s\-]?\d{3}-\d{4})', block_text)
            phone = phone_match.group(1) if phone_match else ""

            if '(pf)' in block_text:
                tag = 'pf'
            else:
                tag = ""

            staff_match = re.search(r'Professional\s+staff\s+(\d+)', block_text, re.IGNORECASE)
            staff = staff_match.group(1) if staff_match else ""

            techs_match = re.search(r'(\d+)\s+technicians', block_text, re.IGNORECASE)
            num_techs = techs_match.group(1) if techs_match else ""

            fields_match = re.search(r'Field of R&D:\s*(.*)', block_text, re.IGNORECASE)
            fields = fields_match.group(1) if fields_match else ""

            # If the code matches one of our known misreads, fix it:
            if code in code_map:
                code = code_map[code]

            return {
                'year': year,   # use the year we extracted
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

        # Very simple: first token is code if it's in code_map
        for line in lines:
            ln = line.strip()
            if not ln:
                continue
            tokens = ln.split(maxsplit=1)
            if not tokens:
                continue

            first_token = tokens[0]
            # if line starts with 'Al','aA','2', etc., treat it as a new block
            if first_token in code_map:
                # finalize old block if present
                if current_code:
                    block_data = save_block(current_code, current_title, current_block_lines)
                    if block_data:
                        data.append(block_data)

                current_code = first_token
                if len(tokens) > 1:
                    current_title = tokens[1].strip()
                else:
                    current_title = ""
                current_block_lines = []
            else:
                if current_code:
                    current_block_lines.append(ln)
                else:
                    # We haven't started a code block yet
                    pass

        # finalize last block
        if current_code:
            block_data = save_block(current_code, current_title, current_block_lines)
            if block_data:
                data.append(block_data)

        return data

    def convert_pdf_to_tiff(self, pdf_path):
        try:
            from pdf2image import convert_from_path
            images = convert_from_path(pdf_path, grayscale=True, fmt='tiff')
            if len(images) == 0:
                self.master.gui.handle_error("Error", f"Error converting PDF to TIFF: {pdf_path}")
                return None
            import tempfile
            temp_dir = tempfile.gettempdir()
            tiff_name = os.path.basename(pdf_path).replace(".pdf", ".tif")
            tiff_path = os.path.join(temp_dir, tiff_name)
            images[0].save(tiff_path, save_all=True, append_images=images[1:])
            return tiff_path
        except Exception as e:
            self.master.gui.handle_error("File Handling Error", f"Unable to open file: {pdf_path}")
            return None

    def save_csv(self, csv_path, parsed_data):
        """
        Instead of automatically saving to Downloads,
        prompt the user for a file name & location using tkinter.filedialog.
        """
        from tkinter import filedialog

        # Prompt user for save location
        chosen_path = filedialog.asksaveasfilename(
            title="Save CSV As",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        # If user canceled, return None
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
