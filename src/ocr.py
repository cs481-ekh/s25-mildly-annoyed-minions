import os
import csv
import re
import platform
import subprocess
import tempfile
import time

import cv2
import numpy as np
import pytesseract
from PIL import Image, ImageSequence
from pdf2image import convert_from_path
from pathlib import Path

from src.config import set_tesseract_path
from src.core.image_processor import ImageProcessor

if platform.system() == "Windows":
    import winreg


class OCRProcessor:
    """Merged OCRProcessor that uses advanced PDF->TIFF pre-processing & splitting,
       then parses extracted text into structured CSV rows."""

    def __init__(self, master):
        self.master = master
        self.temp_dir = tempfile.gettempdir()

        # Any PDFs in this list will *not* be split horizontally.
        self.test_images_no_split = [
            '1975-a1_1-2.pdf',
            '1977-c184_1-5.pdf',
            '1979-a33_1-1.pdf',
            '1982-a15-16_2-1.pdf',
            '1983-a11-12_2-2.pdf',
            '1985-j34-38_5-1.pdf',
            '1986-p255-257_5-3-1-1.pdf',
            '1989-d60_1-2.pdf',
            '1990-a39_1-5.pdf',
            '1992-a361_1-7.pdf',
            '1994-G-g1-see.pdf',
            '1995-3-sees.pdf',
            '1996-page-2_sees-g247.pdf',
        ]

    # ----------------------------------------------------------------------
    # Main extraction entry-point (merged logic)
    # ----------------------------------------------------------------------
    def extract_text_from_pdf(self, pdf_path):
        """
        1) Attempt to set Tesseract path/config.
        2) Extract the year from the PDF filename if available.
        3) Convert PDF to multi-page TIFF (LZW compression, higher DPI).
           - If not in `test_images_no_split`, also split each page horizontally.
        4) For each page in the resulting multi-page TIFF:
           - (Optional) Pre-process with ImageProcessor for better OCR.
           - Perform Tesseract OCR to get text.
        5) Pass the combined text to parse_extracted_text (structured parser).
        6) Return (csv_path, parsed_data) on success, or (None, None) on error.
        """
        # 1) Ensure Tesseract is found
        try:
            set_tesseract_path()
        except FileNotFoundError as e:
            self.master.gui.handle_error("Tesseract Error", str(e))
            return None, None

        # 2) Extract year from filename
        base_name = os.path.basename(pdf_path)
        match = re.match(r'^(\d{4})', base_name)
        year_from_file = match.group(1) if match else "Unknown"

        # 3) Convert PDF to multi-page TIFF (optionally horizontally split)
        tiff_path = self.convert_pdf_to_tiff(pdf_path)
        if not tiff_path:
            return None, None  # Conversion failed

        # 4) For each page in multi-page TIFF -> run OCR
        extracted_text = ""
        try:
            with Image.open(tiff_path) as img_obj:
                for page_index in range(img_obj.n_frames):
                    try:
                        img_obj.seek(page_index)
                        pil_page = img_obj.convert("RGB")  # Ensure RGB for OpenCV
                        np_page = np.array(pil_page)
                        np_page = cv2.cvtColor(np_page, cv2.COLOR_RGB2BGR)

                        # Use your custom image pre-processor if desired
                        # (threshold, morphological ops, etc.)
                        img_processor = ImageProcessor(np_page, split=False)
                        processed_page = img_processor.process_image()  # returns recognized text
                        # If `process_image` returns text directly, we add it:
                        extracted_text += processed_page + "\n"

                        # Alternatively, if `process_image` returns an image, you would then do:
                        #   ocr_ready = img_processor.process_image()
                        #   page_text = pytesseract.image_to_string(ocr_ready, lang='eng', config='--psm 6')
                        #   extracted_text += page_text + "\n"

                    except Exception as e:
                        extracted_text += f"\nError processing page {page_index + 1}: {e}\n"

        except Exception as e:
            # Could not open or read TIFF
            self.master.gui.handle_error("File Handling Error", f"Unable to read TIFF:\n{e}")
            return None, None
        finally:
            # Attempt to clean up the TIFF file
            self.delete_temp_file(tiff_path)

        # 5) Parse the text into structured rows
        parsed_data = self.parse_extracted_text(extracted_text, year_from_file)
        # We'll return a default CSV path (in the same folder as PDF) or the actual path used by `save_csv`.
        csv_path_default = os.path.join(os.path.dirname(pdf_path), base_name.replace(".pdf", ".csv"))

        return csv_path_default, parsed_data

    # ----------------------------------------------------------------------
    # PDF -> TIFF + optional horizontal split (from snippet #1)
    # ----------------------------------------------------------------------
    def convert_pdf_to_tiff(self, pdf_path):
        """Converts the PDF at the input file path to a multi-page TIFF image
           using LZW compression at higher DPI. Also optionally splits pages horizontally."""
        try:
            # Convert to a list of PIL images
            images = convert_from_path(
                pdf_path,
                grayscale=True,
                fmt='tiff',
                dpi=500,
            )
        except Exception as e:
            self.master.gui.handle_error("File Handling Error", f"Unable to open file: {pdf_path}\n{e}")
            return None

        if not images:
            self.master.gui.handle_error("Conversion Error", f"No pages found in PDF: {pdf_path}")
            return None

        # Save the multi-page TIFF in a temp directory
        tiff_name = os.path.basename(pdf_path).replace(".pdf", ".tif")
        tiff_path = os.path.join(self.temp_dir, tiff_name)

        # Combine them into a single multi-page TIFF
        images[0].save(
            tiff_path,
            save_all=True,
            append_images=images[1:],
            compression='tiff_lzw'
        )

        # If the PDF is in `test_images_no_split`, skip the horizontal splitting
        base_name = os.path.basename(pdf_path)
        if base_name in self.test_images_no_split:
            return tiff_path  # Skip splitting

        # Otherwise, re-open the just-saved TIFF and split each page horizontally
        split_pages = []
        try:
            with Image.open(tiff_path) as img:
                page_num = 0
                while True:
                    width, height = img.size
                    # Decide where the middle is; -40 is from snippet #1 for margin
                    middle = (width // 2) - 40

                    left_page = img.crop((0, 0, middle, height))
                    right_page = img.crop((middle, 0, width, height))

                    split_pages.append(left_page)
                    split_pages.append(right_page)

                    page_num += 1
                    img.seek(page_num)
        except EOFError:
            # We simply reached the last page
            pass
        except Exception as e:
            self.master.gui.handle_error("Split Error", f"Error splitting pages:\n{e}")
            return tiff_path  # Return the unsplit TIFF as a fallback

        # Now overwrite the TIFF with these splitted pages
        if split_pages:
            split_pages[0].save(
                tiff_path,
                save_all=True,
                append_images=split_pages[1:],
                compression='tiff_lzw'
            )

        return tiff_path

    # ----------------------------------------------------------------------
    # From snippet #1: remove the TIFF file from the temp directory if possible
    # ----------------------------------------------------------------------
    def delete_temp_file(self, file_path):
        """Try multiple times to delete the temp file; if locked, wait a bit."""
        if not os.path.exists(file_path):
            return
        retries = 5
        delay = 0.1
        for i in range(retries):
            try:
                os.remove(file_path)
                break
            except PermissionError:
                if i < retries - 1:
                    time.sleep(delay)
                    delay *= 1.5
                else:
                    # If still not deletable, just show an error and give up
                    self.master.gui.handle_error("File Deletion Error",
                                                 f"Failed to delete file: {file_path}")

    # ----------------------------------------------------------------------
    # Parsing logic from snippet #2 (block-based)
    # ----------------------------------------------------------------------
    def parse_extracted_text(self, text, year):
        """
        Uses a block-based approach to parse out:
          code, title, street, city, state, zip, phone, etc.
        Returns a list of dicts, each row to be written to CSV.
        """
        lines = text.splitlines()

        # If OCR mistakes occur, map them to correct code
        code_map = {
            "Al": "A1",
            "aA": "A1.1",
            "2": "A1.2",
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

            # Phone (improved regex from snippet #2)
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
                'doctorates': "",  # if you want to parse these, add logic
                'numTechsAndAuxs': num_techs,
                'fields': fields,
                'note': ""  # leftover text or disclaimers can go here
            }

        # Iterate over lines; if a line starts with something that looks like a code, start a new block
        for line in lines:
            ln = line.strip()
            if not ln:
                continue

            tokens = ln.split(maxsplit=1)
            if not tokens:
                continue

            first_token = tokens[0]
            # If recognized as a code (like "A1", or in code_map), start a new block
            if first_token in code_map or re.match(r'^[A-Za-z]\d+', first_token):
                # Save the previous block (if any)
                if current_code:
                    block_data = save_block(current_code, current_title, current_block_lines)
                    if block_data:
                        data.append(block_data)

                current_code = first_token
                current_title = tokens[1].strip() if len(tokens) > 1 else ""
                current_block_lines = []
            else:
                # Accumulate lines in the current block
                if current_code:
                    current_block_lines.append(ln)

        # Final block
        if current_code:
            block_data = save_block(current_code, current_title, current_block_lines)
            if block_data:
                data.append(block_data)

        return data

    # ----------------------------------------------------------------------
    # Saving logic from snippet #2, which writes multiple rows if needed
    # ----------------------------------------------------------------------
    def save_csv(self, pdf_path, parsed_data):
        """
        Automatically saves the CSV file in the user's Downloads directory
        with the same name as the input PDF file.
        """
        try:
            # Get the user's Downloads directory (reusing snippet #1's approach if desired)
            downloads_dir = self.get_downloads_folder()
            os.makedirs(downloads_dir, exist_ok=True)

            # Extract filename from PDF and change extension to .csv
            pdf_filename = os.path.basename(pdf_path)
            csv_filename = os.path.splitext(pdf_filename)[0] + ".csv"
            csv_path = os.path.join(downloads_dir, csv_filename)

            fieldnames = [
                'year', 'code', 'title', 'street', 'city', 'state', 'zip', 'phone',
                'tag', 'staff', 'doctorates', 'numTechsAndAuxs', 'fields', 'note'
            ]

            with open(csv_path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(parsed_data)

            if os.path.exists(csv_path) and os.path.getsize(csv_path) > 0:
                self.master.gui.show_info("File Saved", f"CSV file saved to:\n{csv_path}")
                return csv_path
            else:
                raise Exception("CSV file was not successfully created.")
        except Exception as e:
            # Attempt fallback: save to home folder
            fallback_path = os.path.join(str(Path.home()), csv_filename)
            try:
                with open(fallback_path, mode='w', newline='', encoding='utf-8') as file:
                    writer = csv.DictWriter(file, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(parsed_data)

                self.master.gui.show_info("File Saved", f"CSV file saved to:\n{fallback_path}")
                return fallback_path
            except Exception as fallback_error:
                error_message = (f"Failed to save CSV file: {str(e)}\n"
                                 f"Attempted fallback failed: {str(fallback_error)}")
                self.master.gui.handle_error("File Save Error", error_message)
                return None

    # ----------------------------------------------------------------------
    # (Optional) get_downloads_folder from snippet #1
    # ----------------------------------------------------------------------
    def get_downloads_folder(self):
        """Get the path to the user's Downloads folder, with logic for Windows, macOS, Linux."""
        if platform.system() == "Windows":
            sub_key = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders'
            downloads_guid = '{374DE290-123F-4565-9164-39C4925E467B}'
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key) as key:
                    downloads_folder = winreg.QueryValueEx(key, downloads_guid)[0]
                    return downloads_folder
            except Exception:
                # Default location if registry lookup fails
                return os.path.join(os.path.expanduser("~"), "Downloads")
        elif platform.system() == "Darwin":  # macOS
            return os.path.join(os.path.expanduser("~"), "Downloads")
        else:  # Linux / other
            try:
                xdg_path = subprocess.check_output(['xdg-user-dir', 'DOWNLOAD']).decode().strip()
                if os.path.exists(xdg_path):
                    return xdg_path
            except Exception:
                pass
            # Fallback
            downloads = os.path.join(os.path.expanduser("~"), "Downloads")
            if os.path.exists(downloads):
                return downloads
            return os.path.expanduser("~")
