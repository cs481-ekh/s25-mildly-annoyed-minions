import traceback
import sys
import os
import platform
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed

import cv2
import numpy as np
from PIL import Image

from src.utils.config import set_tesseract_path
from src.core.image_processor import ImageProcessor
from src.utils.ocr_utils import parse_file_to_csv

if platform.system() == "Windows":
    import winreg


def process_pdf_worker(pdf_path, result_queue):
    """Standalone worker for multiprocessing."""
    processor = OCRProcessor(master=None)  # No GUI in multiprocessing context
    csv_path, text = processor.extract_text_from_pdf(pdf_path)
    result_queue.put((csv_path, text) if text else None)


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
        try:
            set_tesseract_path()
        except FileNotFoundError as e:
            self.master.gui.handle_error("Tesseract Error", str(e))
            return None, None

        extracted_text = ""
        basename = os.path.basename(pdf_path)
        filename = basename.replace(".pdf", ".csv")
        downloads_folder = self.get_downloads_folder()
        csv_path = os.path.join(downloads_folder, filename)

        image_path = ImageProcessor.convert_pdf_to_tiff(pdf_path, self.temp_dir)
        if image_path is not None:
            try:
                with Image.open(image_path) as img:
                    num_pages = img.n_frames

                    def process_page(i):
                        img.seek(i)
                        img_cv2 = np.array(img.convert("RGB"))
                        img_cv2 = cv2.cvtColor(img_cv2, cv2.COLOR_RGB2BGR)
                        img_processor = ImageProcessor(
                            img_cv2,
                            split=(
                                False if basename in self.test_images_no_split else True
                            ),
                        )

                        processed_text = img_processor.process_image() + "\n"

                        return processed_text

                    with ThreadPoolExecutor(max_workers=4) as executor:
                        futures = [
                            executor.submit(process_page, i) for i in range(num_pages)
                        ]
                        for future in as_completed(futures):
                            try:
                                extracted_text += future.result() + "\n"
                            except Exception as e:
                                extracted_text += f"\nError: {e}\n"
            finally:
                if os.path.exists(image_path):
                    try:
                        os.remove(image_path)
                    except Exception as e:
                        self.master.gui.handle_error(
                            "File Deletion Error",
                            f"Failed to delete file: {image_path}\n{str(e)}",
                        )

        return csv_path, extracted_text

    def get_downloads_folder(self):
        if platform.system() == "Windows":
            sub_key = (
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
            )
            downloads_guid = "{374DE290-123F-4565-9164-39C4925E467B}"
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key) as key:
                    return winreg.QueryValueEx(key, downloads_guid)[0]
            except Exception:
                return os.path.join(os.path.expanduser("~"), "Downloads")

        elif platform.system() == "Darwin":
            return os.path.join(os.path.expanduser("~"), "Downloads")

        else:
            try:
                xdg_path = (
                    subprocess.check_output(["xdg-user-dir", "DOWNLOAD"])
                    .decode()
                    .strip()
                )
                if os.path.exists(xdg_path):
                    return xdg_path
            except Exception:
                pass
            return os.path.join(os.path.expanduser("~"), "Downloads")

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

            parse_file_to_csv(extracted_text, year, final_csv_path)

            # Notify the user where the file was saved
            self.master.gui.show_info(
                "File Saved", f"CSV file saved to:\n{final_csv_path}"
            )

            return final_csv_path
        except Exception as e:
            error_message = f"Failed to save CSV file: {str(e)}"
            self.master.gui.handle_error("File Save Error", error_message)
            traceback.print_exc(file=sys.stdout)
            return None


class OCRProcessorNoGUI:
    """Class to handle OCR operations, without GUI. Only meant to be used for the Docker image."""

    def __init__(self):
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
        try:
            set_tesseract_path()
        except FileNotFoundError as e:
            return None, None

        extracted_text = ""
        basename = os.path.basename(pdf_path)
        filename = basename.replace(".pdf", ".csv")
        downloads_folder = self.get_downloads_folder()
        csv_path = os.path.join(downloads_folder, filename)

        image_path = ImageProcessor.convert_pdf_to_tiff(pdf_path, self.temp_dir)
        if image_path is not None:
            try:
                with Image.open(image_path) as img:
                    num_pages = img.n_frames

                    def process_page(i):
                        img.seek(i)
                        img_cv2 = np.array(img.convert("RGB"))
                        img_cv2 = cv2.cvtColor(img_cv2, cv2.COLOR_RGB2BGR)
                        img_processor = ImageProcessor(
                            img_cv2,
                            split=(
                                False if basename in self.test_images_no_split else True
                            ),
                        )

                        processed_text = img_processor.process_image() + "\n"

                        return processed_text

                    with ThreadPoolExecutor(max_workers=4) as executor:
                        futures = [
                            executor.submit(process_page, i) for i in range(num_pages)
                        ]
                        for future in as_completed(futures):
                            try:
                                extracted_text += future.result() + "\n"
                            except Exception as e:
                                extracted_text += f"\nError: {e}\n"

            finally:
                if os.path.exists(image_path):
                    try:
                        os.remove(image_path)
                    except Exception as e:
                        print(f"Failed to delete file: {image_path}\n{str(e)}")

        return csv_path, extracted_text

    def get_downloads_folder(self):
        if platform.system() == "Windows":
            sub_key = (
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
            )
            downloads_guid = "{374DE290-123F-4565-9164-39C4925E467B}"
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key) as key:
                    return winreg.QueryValueEx(key, downloads_guid)[0]
            except Exception:
                return os.path.join(os.path.expanduser("~"), "Downloads")

        elif platform.system() == "Darwin":
            return os.path.join(os.path.expanduser("~"), "Downloads")

        else:
            try:
                xdg_path = (
                    subprocess.check_output(["xdg-user-dir", "DOWNLOAD"])
                    .decode()
                    .strip()
                )
                if os.path.exists(xdg_path):
                    return xdg_path
            except Exception:
                pass
            return os.path.join(os.path.expanduser("~"), "Downloads")

    def save_csv(self, csv_path, extracted_text):
        """Saves the extracted text into the CSV file.

        :param csv_path: The path to the CSV file.
        :param extracted_text: The text to be saved.
        :return: Either the path to the CSV file or None.
        """
        try:
            # Get the year from the filename if possible (format like "1975-a1_1-2")
            filename = os.path.basename(csv_path)
            year = ""
            if "-" in filename:
                year_part = filename.split("-")[0]
                if year_part.isdigit() and len(year_part) == 4:
                    year = year_part

            parse_file_to_csv(extracted_text, year, csv_path)

            print(f"Successfully saved to {csv_path}")

            return csv_path
        except Exception as e:
            error_message = f"Failed to save CSV file: {str(e)}"
            print(error_message)
            return None
