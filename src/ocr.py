import os
import csv
import time
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
        # Use the PDF filename but save to Downloads
        filename = os.path.basename(pdf_path).replace(".pdf", ".csv")
        downloads_folder = self.get_downloads_folder()
        csv_path = os.path.join(downloads_folder, filename)

        image_path = self.convert_pdf_to_tiff(pdf_path)  # Get path to TIFF converted image
        if image_path is not None:
            try:
                # Open the image and process it
                with Image.open(image_path) as img:
                    for page_num, frame in enumerate(ImageSequence.Iterator(img)):
                        try:
                            text = pytesseract.image_to_string(frame, lang='eng')
                            extracted_text += text + "\n"
                        except Exception as e:
                            extracted_text += f"\nError processing page {page_num + 1}: {e}\n"
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
                                self.master.gui.handle_error("File Deletion Error",
                                                             f"Failed to delete file: {image_path}")

        return csv_path, extracted_text

    def get_downloads_folder(self):
        """Get the path to the user's Downloads folder"""
        import platform
        import os

        # Get the Downloads directory based on the operating system
        if platform.system() == "Windows":
            import winreg
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

        else:  # Linux and other systems
            try:
                # Try to use the XDG user directories
                import subprocess
                xdg_path = subprocess.check_output(['xdg-user-dir', 'DOWNLOAD']).decode().strip()
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
        try:
            images = convert_from_path(
                pdf_path,
                grayscale=True,
                fmt='tiff',
            )

            # Save TIFF to temp directory to avoid permission issues
            import tempfile
            temp_dir = tempfile.gettempdir()
            tiff_name = os.path.basename(pdf_path).replace(".pdf", ".tif")
            tiff_path = os.path.join(temp_dir, tiff_name)

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
            # Ensure we're saving to the Downloads folder
            downloads_folder = self.get_downloads_folder()
            filename = os.path.basename(csv_path)
            final_csv_path = os.path.join(downloads_folder, filename)

            # Get the year from the filename if possible (format like "1975-a1_1-2")
            year = ''
            if '-' in filename:
                year_part = filename.split('-')[0]
                if year_part.isdigit() and len(year_part) == 4:
                    year = year_part

            with open(final_csv_path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)

                # Write the header with all columns from the example CSV
                writer.writerow([
                    'year', 'code', 'title', 'street', 'city', 'state', 'zip', 'phone',
                    'tag', 'staff', 'doctorates', 'numTechsAndAuxs', 'fields', 'note'
                ])

                # Create a row with the year from the filename and extracted text in the notes field
                writer.writerow([
                    year,  # year from filename or empty
                    '',  # code
                    '',  # title
                    '',  # street
                    '',  # city
                    '',  # state
                    '',  # zip
                    '',  # phone
                    '',  # tag
                    '',  # staff
                    '',  # doctorates
                    '',  # numTechsAndAuxs
                    '',  # fields
                    extracted_text  # note - full text for you to parse later
                ])

            # Notify the user where the file was saved
            self.master.gui.show_info("File Saved", f"CSV file saved to:\n{final_csv_path}")

            return final_csv_path
        except Exception as e:
            error_message = f"Failed to save CSV file: {str(e)}"
            self.master.gui.handle_error("File Save Error", error_message)
            return None