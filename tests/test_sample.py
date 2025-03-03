import os

from src.ocr import OCRProcessor


def test_sample():
    csv_path, extracted_text = OCRProcessor.extract_text_from_pdf("../resources/test-ocr.pdf")
    OCRProcessor.save_csv(csv_path, extracted_text)
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