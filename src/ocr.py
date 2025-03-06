import csv
import os
import tempfile
import time

import pytesseract
from PIL import Image, ImageSequence
from pdf2image import convert_from_path

from src.config import set_tesseract_path


class OCRProcessor:
    def __init__(self, master):
        self.master = master
        self.temp_dir = tempfile.gettempdir()
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
                            text = pytesseract.image_to_string(frame, lang='eng', config='--psm 6 --oem 2')
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
                dpi=300,
            )

            # Save TIFF to temp directory to avoid permission issues
            tiff_name = os.path.basename(pdf_path).replace(".pdf", ".tif")
            tiff_path = os.path.join(self.temp_dir, tiff_name)

            if len(images) != 0:
                images[0].save(tiff_path, save_all=True, append_images=images[1:], compression='tiff_lzw')
            else:
                self.master.gui.handle_error("Error", f"Error converting PDF to TIFF: {pdf_path}")
                return None

            if os.path.basename(pdf_path) in self.test_images_no_split:
                print('Skipping test image')
                return tiff_path

            img = Image.open(tiff_path)
            page_num = 0
            split_images = []

            while True:
                width, height = img.size
                middle = (width // 2) - 40

                left_h = img.crop((0, 0, middle, height))
                right_h = img.crop((middle, 0, width, height))

                split_images.append(left_h)
                split_images.append(right_h)

                page_num += 1
                try:
                    img.seek(page_num)
                except EOFError:
                    break

            split_images[0].save(tiff_path, save_all=True, append_images=split_images[1:])

            return tiff_path
        except Exception as e:
            self.master.gui.handle_error("File Handling Error", f"Unable to open file: {pdf_path}")
            return None


    def clean_text(self, extracted_text):
        """Cleans text into the expected format.

        Returns the cleaned text in CSV-ready format (DataFrame, list of rows, etc.)"""
        # TODO: Will be implemented in a Sprint after Sprint 2.
        try:
            return extracted_text
        except Exception as e:
            error_message = f"Failed to save CSV file: {str(e)}"
            self.master.gui.handle_error("Cleaning Error", error_message)
            return extracted_text


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