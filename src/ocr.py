import csv
import os
import platform
import subprocess
import tempfile
import time

import cv2
import numpy as np
from pdf2image import convert_from_path
from PIL import Image

from src.config import set_tesseract_path
from src.core.image_processor import ImageProcessor

if platform.system() == "Windows":
    import winreg


class OCRProcessor:
    """Class to handle OCR operations."""

    def __init__(self, master):
        self.master = master
        self.temp_dir = tempfile.gettempdir()
        self.test_images_no_split = [
            "1975-a1_1-2.pdf",
            "1977-c184_1-5.pdf",
            "1979-a33_1-1.pdf",
            "1982-a15-16_2-1.pdf",
            "1983-a11-12_2-2.pdf",
            "1985-j34-38_5-1.pdf",
            "1986-p255-257_5-3-1-1.pdf",
            "1989-d60_1-2.pdf",
            "1990-a39_1-5.pdf",
            "1992-a361_1-7.pdf",
            "1994-G-g1-see.pdf",
            "1995-3-sees.pdf",
            "1996-page-2_sees-g247.pdf",
            "test-ocr.pdf",
        ]

    def extract_text_from_pdf(self, pdf_path):
        """Extracts all text from the PDF at the input file path.

        :param pdf_path: The path to the PDF file.
        :return: A tuple in which the first element is the path where the final CSV should be made
         and the second element is the extracted text on success and on failure both elements will
         be None.
        """
        try:
            set_tesseract_path()  # Call the function from config.py
        except FileNotFoundError as e:
            self.master.gui.handle_error("Tesseract Error", str(e))
            return None, None

        extracted_text = ""
        # Use the PDF filename but save to Downloads
        basename = os.path.basename(pdf_path)
        filename = basename.replace(".pdf", ".csv")
        downloads_folder = self.get_downloads_folder()
        csv_path = os.path.join(downloads_folder, filename)

        image_path = self.convert_pdf_to_tiff(
            pdf_path
        )  # Get path to TIFF converted image
        if image_path is not None:
            try:
                # Open the image and process it
                with Image.open(image_path) as img:
                    for i in range(img.n_frames):  # For each page in the image
                        try:
                            # Move to the page
                            img.seek(i)

                            # Convert to an OpenCV compatible format
                            img_cv2 = np.array(img.convert("RGB"))
                            img_cv2 = cv2.cvtColor(img_cv2, cv2.COLOR_RGB2BGR)

                            # Pass to ImageProcessor
                            img_processor = ImageProcessor(
                                img_cv2,
                                split=False
                                if basename in self.test_images_no_split
                                else True,
                            )

                            # Extract text
                            extracted_text += img_processor.process_image() + "\n"
                        except Exception as e:
                            extracted_text += f"\nError processing page {i + 1}: {e}\n"
            finally:
                # Ensure the file is closed and released
                if os.path.exists(image_path):
                    retries = 0
                    delay = 0.00001
                    for i in range(retries):
                        try:
                            os.remove(image_path)
                            break
                        except PermissionError:
                            if i < retries - 1:
                                time.sleep(delay)
                                delay *= 1.1
                            else:
                                self.master.gui.handle_error(
                                    "File Deletion Error",
                                    f"Failed to delete file: {image_path}",
                                )

        return csv_path, extracted_text

    def get_downloads_folder(self):
        """Get the path to the user's Downloads folder

        :return: The path to the user's Downloads folder
        """
        # Get the Downloads directory based on the operating system
        if platform.system() == "Windows":
            sub_key = (
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
            )
            downloads_guid = "{374DE290-123F-4565-9164-39C4925E467B}"

            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key) as key:
                    downloads_folder = winreg.QueryValueEx(key, downloads_guid)[0]
                    return downloads_folder
            except Exception:
                # Default location if registry lookup fails
                return os.path.join(os.path.expanduser("~"), "Downloads")

        elif platform.system() == "Darwin":  # macOS
            return os.path.join(os.path.expanduser("~"), "Downloads")

        else:  # Linux and other systems
            try:
                # Try to use the XDG user directories
                xdg_path = (
                    subprocess.check_output(["xdg-user-dir", "DOWNLOAD"])
                    .decode()
                    .strip()
                )
                if os.path.exists(xdg_path):
                    return xdg_path
            except Exception:
                pass

            # Fallback to ~/Downloads
            downloads = os.path.join(os.path.expanduser("~"), "Downloads")
            if os.path.exists(downloads):
                return downloads

            # Last resort: use home directory
            return os.path.expanduser("~")

    def convert_pdf_to_tiff(self, pdf_path):
        """Converts the PDF at the input file path to a multipage TIFF image using LZW compression.

        :param pdf_path: The path to a PDF file.
        :return: The path to a TIFF image on success or None if there was an error.
        """
        try:
            images = convert_from_path(
                pdf_path,
                grayscale=True,
                fmt="tiff",
                dpi=500,
            )

            # Save TIFF to temp directory to avoid permission issues
            tiff_name = os.path.basename(pdf_path).replace(".pdf", ".tif")
            tiff_path = os.path.join(self.temp_dir, tiff_name)

            if len(images) != 0:
                images[0].save(
                    tiff_path,
                    save_all=True,
                    append_images=images[1:],
                    compression="tiff_lzw",
                )
            else:
                self.master.gui.handle_error(
                    "Error", f"Error converting PDF to TIFF: {pdf_path}"
                )
                return None

            if os.path.basename(pdf_path) in self.test_images_no_split:
                print("Skipping test image")

            return tiff_path
        except Exception:
            self.master.gui.handle_error(
                "File Handling Error", f"Unable to open file: {pdf_path}"
            )
            return None

    def clean_text(self, extracted_text):
        """Cleans text into the expected format.

        :return: The cleaned text in CSV-ready format (DataFrame, list of rows, etc.)"""
        # TODO: Will be implemented in a Sprint after Sprint 2.
        try:
            return extracted_text
        except Exception as e:
            error_message = f"Failed to save CSV file: {str(e)}"
            self.master.gui.handle_error("Cleaning Error", error_message)
            return extracted_text

    def save_csv(self, csv_path, extracted_text):
        """Saves the extracted text into the CSV file.

        :param csv_path: The path to the CSV file.
        :param extracted_text: The text to be saved.
        :return: Either the path to the CSV file or None.
        """
        try:
            # Ensure we're saving to the Downloads folder
            downloads_folder = self.get_downloads_folder()
            filename = os.path.basename(csv_path)
            final_csv_path = os.path.join(downloads_folder, filename)

            # Get the year from the filename if possible (format like "1975-a1_1-2")
            year = ""
            if "-" in filename:
                year_part = filename.split("-")[0]
                if year_part.isdigit() and len(year_part) == 4:
                    year = year_part

            with open(final_csv_path, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)

                # Write the header with all columns from the example CSV
                writer.writerow(
                    [
                        "year",
                        "code",
                        "title",
                        "street",
                        "city",
                        "state",
                        "zip",
                        "phone",
                        "tag",
                        "staff",
                        "doctorates",
                        "numTechsAndAuxs",
                        "fields",
                        "note",
                    ]
                )

                # Create a row with the year from the filename and extracted text in the notes field
                writer.writerow(
                    [
                        year,  # year from filename or empty
                        "",  # code
                        "",  # title
                        "",  # street
                        "",  # city
                        "",  # state
                        "",  # zip
                        "",  # phone
                        "",  # tag
                        "",  # staff
                        "",  # doctorates
                        "",  # numTechsAndAuxs
                        "",  # fields
                        extracted_text,  # note - full text for you to parse later
                    ]
                )

            # Notify the user where the file was saved
            self.master.gui.show_info(
                "File Saved", f"CSV file saved to:\n{final_csv_path}"
            )

            return final_csv_path
        except Exception as e:
            error_message = f"Failed to save CSV file: {str(e)}"
            self.master.gui.handle_error("File Save Error", error_message)
            return None
