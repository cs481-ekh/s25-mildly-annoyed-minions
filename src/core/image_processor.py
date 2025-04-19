import tempfile
import os

import cv2
import pytesseract
from pdf2image import convert_from_path

from src.utils.logger import get_logger

logger = get_logger("image_processor")


WHITELIST = """ !\\"#$%&\\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]`abcdefghijklmnopqrstuvwxyz{|}"""
BLACKLIST = """~_^"""
tess_config = config = (
    f"--psm 6 -c tessedit_char_whitelist={WHITELIST} -c tessedit_char_blacklist={BLACKLIST}"
)


class ImageProcessor:
    def __init__(self, image, split=True):
        self.image = image
        self.split = split

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
            (cnt, cv2.boundingRect(cnt))
            for cnt in contours
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

    def process_image(self):
        """
        Processes the image.

        :return: The full text of the page.
        """
        if self.split:
            left_col, right_col = self.split_page()
            left_paths, right_paths = self.process_half(left_col), self.process_half(
                right_col
            )

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

    @staticmethod
    def convert_pdf_to_tiff(pdf_path, temp_dir):
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
            tiff_path = os.path.join(temp_dir, tiff_name)

            if len(images) != 0:
                images[0].save(
                    tiff_path,
                    save_all=True,
                    append_images=images[1:],
                    compression="tiff_lzw",
                )
            else:
                logger.error(f"Could not convert {pdf_path} to TIFF.")
                return None

            return tiff_path
        except Exception as e:
            print(f"Error convert PDF to TIFF: {e}")
            logger.error(f"Error converting {pdf_path} to TIFF: {e}")
            return None
