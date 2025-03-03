import os
import pytest
from unittest.mock import MagicMock
from src.ocr import OCRProcessor

# Mock the master object (assuming it has a 'gui' attribute with a 'handle_error' method)
mock_master = MagicMock()
mock_master.gui.handle_error = MagicMock()

@pytest.mark.parametrize("pdf_path", [
    "../resources/test-entries/pdfs/1975-a1_1-2.pdf",
    "../resources/test-entries/pdfs/1977-c184_1-5.pdf",
    "../resources/test-entries/pdfs/1979-a33_1-1.pdf",
    "../resources/test-entries/pdfs/1982-a15-16_2-1.pdf",
    "../resources/test-entries/pdfs/1983-a11-12_2-2.pdf",
    "../resources/test-entries/pdfs/1985-j34-38_5-1.pdf",
    "../resources/test-entries/pdfs/1986-p255-257_5-3-1-1.pdf",
    "../resources/test-entries/pdfs/1987-page468.pdf",
    "../resources/test-entries/pdfs/1988-page555.pdf",
    "../resources/test-entries/pdfs/1989-d60_1-2.pdf",
    "../resources/test-entries/pdfs/1990-a39_1-5.pdf",
    "../resources/test-entries/pdfs/1991-page314.pdf",
    "../resources/test-entries/pdfs/1992-a361_1-7.pdf",
    "../resources/test-entries/pdfs/1993-page566.pdf",
    "../resources/test-entries/pdfs/1994-G-g1-see.pdf",
    "../resources/test-entries/pdfs/1995-3-sees.pdf",
    "../resources/test-entries/pdfs/1996-page-2_sees-g247.pdf",
    "../resources/test-entries/pdfs/1997-large-corp.pdf",
    "../resources/test-entries/pdfs/1998-page305.pdf",
])
@pytest.mark.slow
def test_parsing(pdf_path):
    # Instantiate OCRProcessor with the mock master
    ocr_processor = OCRProcessor(mock_master)

    # Call the extract_text_from_pdf method
    csv_path, extracted_text = ocr_processor.extract_text_from_pdf(pdf_path)

    # Ensure the extracted text is not None and not empty
    assert extracted_text is not None, "Returned text is None"
    assert extracted_text.strip(), "Returned text is empty after trimming"

    # Save the extracted text to a CSV file
    saved_csv_path = ocr_processor.save_csv(csv_path, extracted_text)

    # Ensure the CSV file was saved successfully
    assert saved_csv_path is not None, "Failed to save CSV file"

    # Clean up: Remove the CSV file after the test
    if os.path.exists(saved_csv_path):
        os.remove(saved_csv_path)