import os
from unittest.mock import MagicMock

import pytest

from src.ocr import OCRProcessor

# Mock the master object (assuming it has a 'gui' attribute with a 'handle_error' method)
mock_master = MagicMock()
mock_master.gui.handle_error = MagicMock()


@pytest.mark.quick
def test_sample():
    ocr_processor = OCRProcessor(mock_master)
    csv_path, extracted_text = ocr_processor.extract_text_from_pdf(pdf_path="../resources/test-ocr.pdf")
    ocr_processor.save_csv(csv_path, extracted_text)

    assert extracted_text is not None, "Returned text is None"
    assert csv_path is not None, "Returned CSV path is None"

    assert extracted_text.strip(), "Returned text is empty after trimming"

    checks = [
        "This file contains some words.",
        "This file also contains text.",
        "This second part of the text is in Page 2"
    ]
    for check_num, check in enumerate(checks):
        assert check in extracted_text, f"Sentence {check_num + 1} is missing from the parsed text"

    assert os.path.exists(csv_path), f"CSV path {csv_path} does not exist"
    os.remove(csv_path)