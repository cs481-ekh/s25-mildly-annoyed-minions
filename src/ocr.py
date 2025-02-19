import fitz
import pytesseract
from PIL import Image
import io


def extract_text_from_pdf(pdf_path):

    extracted_text = ""

    # Open the PDF file
    pdf_document = fitz.open(pdf_path)

    # Iterate through each page
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)

        # Get the image of the page
        pix = page.get_pixmap()
        img = Image.open(io.BytesIO(pix.tobytes()))

        # Use Tesseract to do OCR on the image
        text = pytesseract.image_to_string(img)
        extracted_text += text + "\n"

    return extracted_text