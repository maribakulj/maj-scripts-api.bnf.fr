import io
import pytest
from pypdf import PdfReader

from bnf_p0.pdf_build import DEFAULT_DPI, jpeg_info, jpegs_to_pdf

# JPEG minimal 8x8 en niveaux de gris. APP0 : unités = 1 (dpi), densité 72.
JPEG = bytes.fromhex(
    "ffd8ffe000104a46494600010101004800480000ffdb004300"
    + "10" * 64
    + "ffc0000b080008000801011100ffc40014000100000000000000000000000000000009"
    "ffda0008010100003f00d2cf20ffd9"
)


def test_jpeg_dimensions_and_density_are_read():
    width, height, components, dpi = jpeg_info(JPEG)
    assert (width, height, components) == (8, 8, 1)
    assert dpi == 72.0


def test_density_falls_back_when_the_file_declares_no_unit():
    # unités = 0 : le JFIF ne donne qu'un rapport d'aspect, pas une résolution.
    sans_unite = JPEG.replace(bytes.fromhex("010100480048"), bytes.fromhex("010000010001"), 1)
    assert jpeg_info(sans_unite)[3] == DEFAULT_DPI


def test_non_jpeg_is_refused():
    with pytest.raises(ValueError):
        jpeg_info(b"\x89PNG\r\n\x1a\n")


def test_pdf_has_one_page_per_image_and_opens():
    pdf = jpegs_to_pdf([JPEG, JPEG, JPEG])
    assert pdf.startswith(b"%PDF-")
    reader = PdfReader(io.BytesIO(pdf))
    assert len(reader.pages) == 3


def test_page_box_follows_image_density():
    reader = PdfReader(io.BytesIO(jpegs_to_pdf([JPEG])))
    box = reader.pages[0].mediabox
    assert round(float(box.width)) == 8      # 8 px à 72 dpi = 8 points
    assert round(float(box.height)) == 8


def test_empty_input_is_refused():
    with pytest.raises(ValueError):
        jpegs_to_pdf([])
