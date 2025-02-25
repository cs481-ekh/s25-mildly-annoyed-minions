# config.py
import os
import platform
import pytesseract

def set_tesseract_path():
    system = platform.system()
    if system == "Windows":
        possible_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"
        ]
    elif system == "Darwin":
        possible_paths = ["/usr/local/bin/tesseract", "/opt/homebrew/bin/tesseract"]
    else:
        possible_paths = ["/usr/bin/tesseract", "/usr/local/bin/tesseract"]

    for path in possible_paths:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            return

    raise FileNotFoundError("Tesseract is not installed or not found.")

set_tesseract_path()
