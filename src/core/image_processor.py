import cv2
import numpy as np
import pytesseract

WHITELIST = """ !\\"#$%&\\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]`abcdefghijklmnopqrstuvwxyz{|}"""
BLACKLIST = """~_^"""
tess_config = config = (
    f"--psm 6 -c tessedit_char_whitelist={WHITELIST} -c tessedit_char_blacklist={BLACKLIST}"
)


class ImageProcessor:
    def __init__(self, image, split=True):
        self.image = image
        self.split = split

    def sharpen_image(self):
        """
        Sharpens the image.

        :return: None. Updates the `ImageProcessor.image` attribute itself.
        """
        sharpen_kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])

        self.image = cv2.filter2D(self.image, -1, sharpen_kernel)

    def split_page(self):
        """
        Splits the image into two halves.

        :return: The two halves.
        """
        height, width, _ = self.image.shape
        middle = width // 2

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
        ret, thresh = cv2.threshold(
            gray, 128, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY_INV
        )

        # Draw the fake-boxes
        rect_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (200, 20))
        dilation = cv2.dilate(thresh, rect_kernel, iterations=1)

        cv2.imwrite("dilation.tiff", dilation)

        # Draw the bounding boxes based on the fake ones
        contours, hierarchy = cv2.findContours(
            dilation, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        min_width = 1000  # Remove very narrow shapes
        min_height = 60  # Remove very short shapes

        boxes = []
        max_w = 0
        max_h = 0
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if w > min_width and h > min_height:
                region = image[y : y + h, x : x + w].copy()

                shifted_contour = cnt - [x, y]
                cv2.drawContours(region, [shifted_contour], -1, (0, 255, 0), 2)

                boxes.append(region)
                max_w = max(max_w, w)
                max_h = max(max_h, h)
        total_h = sum([b.shape[0] for b in boxes])
        total_w = max([b.shape[1] for b in boxes])
        stacked = np.ones((total_h, total_w, 3), dtype=np.uint8) * 255

        current_y = 0
        boxes.reverse()
        for box in boxes:
            h, w = box.shape[:2]
            stacked[current_y : current_y + h, 0:w] = box
            current_y += h

        return stacked

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
                left, lang="eng", config=tess_config
            ).replace("|", "1")

            right_text = pytesseract.image_to_string(
                right, lang="eng", config=tess_config
            ).replace("|", "1")

            return left_text + "\n" + right_text
        else:
            processed = self.process_half(self.image)
            text = pytesseract.image_to_string(
                processed, lang="eng", config=tess_config
            ).replace("|", "1")

            return text
