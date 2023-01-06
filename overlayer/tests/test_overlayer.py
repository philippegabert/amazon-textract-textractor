import os
import logging
import textractoverlayer.image_tools as it

def test_overlayer_pdf_dimensions(caplog):
    caplog.set_level(logging.DEBUG)
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    input_filename = os.path.join(SCRIPT_DIR, "data/Amazon-Textract-Pdf.pdf")
    dimensions = it.get_width_height_from_file(input_filename)
    for page_dimensions in dimensions:
        assert page_dimensions.doc_height == 792
        assert page_dimensions.doc_width == 612

