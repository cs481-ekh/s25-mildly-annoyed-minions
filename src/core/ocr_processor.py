import os
import platform
from src.core.image_processor import ImageProcessor
if platform.system() == "Windows":
    import winreg


class OCRProcessor:
    """Class to handle OCR operations."""
    def __init__(self):
        # A list of PDF filenames for which image splitting is not applied.
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
        """
        Delegate the PDF-to-text extraction to the ImageProcessor class.
        Returns a tuple (csv_path, extracted_text) or (None, None) on failure.
        """
        return ImageProcessor.extract_text_from_pdf(pdf_path, self.test_images_no_split, self.master.gui)

    def save_csv(self, csv_path, extracted_text):
        """Saves the extracted text into a CSV file."""
        try:
            # Delegate this functionality to the ImageProcessor (or leave as is)
            # Here we keep the existing logic.
            downloads_folder = ImageProcessor.get_downloads_folder()
            filename = os.path.basename(csv_path)
            final_csv_path = os.path.join(downloads_folder, filename)

            # Get the year from the filename if possible (format like "1975-a1_1-2")
            year = ""
            if "-" in filename:
                year_part = filename.split("-")[0]
                if year_part.isdigit() and len(year_part) == 4:
                    year = year_part

            import csv
            with open(final_csv_path, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
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
                writer.writerow(
                    [
                        year,  # year from filename or empty
                        "",    # code
                        "",    # title
                        "",    # street
                        "",    # city
                        "",    # state
                        "",    # zip
                        "",    # phone
                        "",    # tag
                        "",    # staff
                        "",    # doctorates
                        "",    # numTechsAndAuxs
                        "",    # fields
                        extracted_text,  # note - full text for later parsing
                    ]
                )

            # self.master.gui.show_info("File Saved", f"CSV file saved to:\n{final_csv_path}")
            return final_csv_path
        except Exception as e:
            # error_message = f"Failed to save CSV file: {str(e)}"
            # self.master.gui.handle_error("File Save Error", error_message)
            return None
