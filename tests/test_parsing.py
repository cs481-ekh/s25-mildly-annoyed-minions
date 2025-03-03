import os

import pytest

from src.ocr import OCRProcessor


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
    csv_path, extracted_text = OCRProcessor.extract_text_from_pdf(pdf_path)
    OCRProcessor.save_csv(csv_path, extracted_text)
    os.remove(csv_path)

    assert extracted_text is not None, "Returned text is None"
    assert extracted_text.strip(), "Returned text is empty after trimming"
