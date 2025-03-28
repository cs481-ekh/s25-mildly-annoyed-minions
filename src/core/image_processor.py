import cv2
import pytesseract
import numpy as np

WHITELIST = """ !\\"#$%&\\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]`abcdefghijklmnopqrstuvwxyz{|}"""
BLACKLIST = """~_^"""
tess_config = config=f"--psm 6 -c tessedit_char_whitelist={WHITELIST} -c tessedit_char_blacklist={BLACKLIST}"

class ImageProcessor:
    def __init__(self, image, split=True):
        self.image = image
        self.split = split

    def sharpen_image(self):
        """
        Sharpens the image.

        :return: None. Updates the `ImageProcessor.image` attribute itself.
        """
        sharpen_kernel = np.array([
            [-1, -1, -1],
            [-1,  9, -1],
            [-1, -1, -1]
        ])

        self.image = cv2.filter2D(self.image, -1, sharpen_kernel)

    def split_page(self):
        """
        Splits the image into two halves.

        :return: The two halves.
        """
        height, width, _ = self.image.shape
        middle = (width // 2)

        left_col = self.image[:-100, 125:middle]
        right_col = self.image[:-100, middle:-110]

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
        ret, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY_INV)

        # Draw the fake-boxes
        rect_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (200, 20))
        dilation = cv2.dilate(thresh, rect_kernel, iterations=1)

        # Draw the bounding boxes based on the fake ones
        image2 = image.copy()
        contours, hierarchy = cv2.findContours(dilation, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
        cv2.drawContours(image2, contours, -1, (0, 255, 0), 3)

        # Return the boxed image
        return image2

    def process_image(self):
        """
        Processes the image.

        :return: The full text of the page.
        """
        self.sharpen_image()
        if self.split:
            left_col, right_col = self.split_page()
            left, right = self.process_half(left_col), self.process_half(right_col)

            left_text = pytesseract.image_to_string(
                left,
                lang='eng',
                config=tess_config
            ).replace("|", "1")

            right_text = pytesseract.image_to_string(
                right,
                lang='eng',
                config=tess_config
            ).replace("|", "1")

            return left_text + "\n" + right_text
        else:
            processed = self.process_half(self.image)
            text = pytesseract.image_to_string(
                processed,
                lang='eng',
                config=tess_config
            ).replace("|", "1")

            return text
