import os
import platform
import subprocess
import tempfile
import time

import cv2
import numpy as np
from pdf2image import convert_from_path
from PIL import Image
import pytesseract

from src.utils.config import set_tesseract_path

if platform.system() == "Windows":
    import winreg


WHITELIST = """ !\\"#$%&\\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]`abcdefghijklmnopqrstuvwxyz{|}"""
BLACKLIST = """~_^"""
tess_config = config = (
    f"--psm 6 -c tessedit_char_whitelist={WHITELIST} -c tessedit_char_blacklist={BLACKLIST}"
)


class ImageProcessor:
    """
    Class to handle image processing tasks.
    This includes converting PDFs to TIFF images, processing each image for OCR,
    and retrieving helper paths.
    """

    def __init__(self, image, split=True):
        """
        Initialize the ImageProcessor with an image.

        Parameters:
            image (numpy.ndarray): The image data (in BGR format).
            split (bool): Whether to perform splitting or additional processing if needed.
        """
        self.image = image
        self.split = split

    def process_image(self):
        """
        Processes the image.

        :return: The full text of the page.
        """
        if self.split:
            left_col, right_col = self.split_page()
            left_paths, right_paths = self.process_half(left_col), self.process_half(right_col)

            text = ""

            for tmp_file in left_paths:
                img = cv2.imread(tmp_file)
                text += pytesseract.image_to_string(
                    img, lang="eng", config=tess_config
                ).replace("|", "1")
                text += "\n"
                os.remove(tmp_file)
            for tmp_file in right_paths:
                img = cv2.imread(tmp_file)
                text += pytesseract.image_to_string(
                    img, lang="eng", config=tess_config
                ).replace("|", "1")
                text += "\n"
                os.remove(tmp_file)

            return text
        else:
            processed_paths = self.process_half(self.image)

            text = ""

            for tmp_file in processed_paths:
                img = cv2.imread(tmp_file)
                text += pytesseract.image_to_string(
                    img, lang="eng", config=tess_config
                ).replace("|", "1")
                text += "\n"
                os.remove(tmp_file)

            return text

    def split_page(self):
        """
        Splits the image into two halves.

        :return: The two halves.
        """
        height, width, _ = self.image.shape
        middle = width // 2

        left_col = self.image[:, :middle]
        right_col = self.image[:, middle:]

        return left_col, right_col

    @staticmethod
    def process_half(image):
        """
        Processes a single half of the image.

        :param image: One half of the image.
        :return: The half of the image with bounding boxes.
        """
        # Grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Binarization
        _, thresh = cv2.threshold(
            gray, 128, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY_INV
        )

        # Draw the fake-boxes
        rect_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (200, 20))
        dilation = cv2.dilate(thresh, rect_kernel, iterations=1)

        # Draw the bounding boxes based on the fake ones
        contours, _ = cv2.findContours(
            dilation, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        min_height = 60  # Remove very short shapes
        file_paths = []

        # Pair each contour with its bounding box, filter by height, and sort by y-position descending
        contour_boxes = [
            (cnt, cv2.boundingRect(cnt)) for cnt in contours
            if cv2.boundingRect(cnt)[3] > min_height
        ]
        contour_boxes.sort(key=lambda cb: cb[1][1], reverse=False)  # Sort by y

        for cnt, (x, y, w, h) in contour_boxes:
            region = image[y : y + h, x : x + w].copy()
            shifted_contour = cnt - [x, y]
            cv2.drawContours(region, [shifted_contour], -1, (0, 255, 0), 2)

            # Create a temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".tiff")
            cv2.imwrite(temp_file.name, region)
            file_paths.append(temp_file.name)

        return file_paths

    @staticmethod
    def convert_pdf_to_tiff(pdf_path, gui):
        """
        Converts a PDF file to a multipage TIFF image using LZW compression.

        Parameters:
            pdf_path (str): The file path to the PDF.
            gui: The GUI instance for error reporting.

        Returns:
            str: The file path to the generated TIFF image, or None if conversion fails.
        """
        try:
            images = convert_from_path(pdf_path, grayscale=True, fmt="tiff", dpi=500)
            tiff_name = os.path.basename(pdf_path).replace(".pdf", ".tif")
            temp_dir = tempfile.gettempdir()
            tiff_path = os.path.join(temp_dir, tiff_name)

            if images:
                images[0].save(tiff_path, save_all=True, append_images=images[1:], compression="tiff_lzw")
            else:
                gui.handle_error("Error", f"Error converting PDF to TIFF: {pdf_path}")
                return None

            return tiff_path
        except Exception as ex:
            gui.handle_error("File Handling Error", f"Unable to convert PDF to TIFF: {pdf_path}\n{ex}")
            return None

    @staticmethod
    def extract_text_from_pdf(pdf_path, test_images_no_split, gui):
        """
        Extract text from a PDF file by converting it to a TIFF image and processing each frame.

        Parameters:
            pdf_path (str): Path to the PDF file.
            test_images_no_split (list): List of filenames where splitting is not applied.
            gui: The GUI instance for error reporting.

        Returns:
            tuple: (csv_path, extracted_text) where csv_path is the target CSV file path and
                   extracted_text is the concatenated OCR result. Returns (None, None) on error.
        """
        try:
            set_tesseract_path()
        except FileNotFoundError as e:
            gui.handle_error("Tesseract Error", str(e))
            return None, None

        extracted_text = ""
        basename = os.path.basename(pdf_path)
        filename = basename.replace(".pdf", ".csv")
        downloads_folder = ImageProcessor.get_downloads_folder()
        csv_path = os.path.join(downloads_folder, filename)

        tiff_path = ImageProcessor.convert_pdf_to_tiff(pdf_path, gui)
        if tiff_path is not None:
            try:
                with Image.open(tiff_path) as img:
                    for i in range(img.n_frames):
                        try:
                            img.seek(i)
                            # Convert image to RGB and then to BGR (if needed by pytesseract)
                            img_rgb = img.convert("RGB")
                            img_cv2 = np.array(img_rgb)
                            img_cv2 = cv2.cvtColor(img_cv2, cv2.COLOR_RGB2BGR)
                            # Decide whether to split/process differently based on filename.
                            should_split = False if basename in test_images_no_split else True
                            processor_instance = ImageProcessor(img_cv2, split=should_split)
                            extracted_text += processor_instance.process_image() + "\n"
                        except Exception as e:
                            extracted_text += f"\nError processing page {i + 1}: {e}\n"
            finally:
                # Attempt to delete the temporary TIFF with a few retries.
                retries = 3
                delay = 0.1
                for attempt in range(retries):
                    try:
                        if os.path.exists(tiff_path):
                            os.remove(tiff_path)
                        break
                    except PermissionError:
                        if attempt < retries - 1:
                            time.sleep(delay)
                            delay *= 1.5
                        else:
                            gui.handle_error("File Deletion Error", f"Failed to delete file: {tiff_path}")
            return csv_path, extracted_text
        else:
            return None, None

    @staticmethod
    def get_downloads_folder():
        """
        Retrieves the user's Downloads folder path based on the operating system.

        Returns:
            str: The path to the Downloads folder.
        """
        if platform.system() == "Windows":
            sub_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
            downloads_guid = "{374DE290-123F-4565-9164-39C4925E467B}"
            try:
                import winreg
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key) as key:
                    downloads_folder = winreg.QueryValueEx(key, downloads_guid)[0]
                    return downloads_folder
            except Exception:
                return os.path.join(os.path.expanduser("~"), "Downloads")
        elif platform.system() == "Darwin":
            return os.path.join(os.path.expanduser("~"), "Downloads")
        else:
            try:
                xdg_path = subprocess.check_output(["xdg-user-dir", "DOWNLOAD"]).decode().strip()
                if os.path.exists(xdg_path):
                    return xdg_path
            except Exception:
                pass
            downloads = os.path.join(os.path.expanduser("~"), "Downloads")
            return downloads if os.path.exists(downloads) else os.path.expanduser("~")