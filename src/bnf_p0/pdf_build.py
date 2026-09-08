"""Fabrication d'un PDF à partir d'images JPEG IIIF.

Gallica n'expose aucune route API produisant un PDF : le suffixe `.pdf` est une
URL du site web, désormais protégée. Reconstruire le PDF à partir des images
IIIF est donc le seul chemin qui reste entièrement dans les API.

Les JPEG sont insérés tels quels (filtre PDF `DCTDecode`) : aucune
recompression, aucune perte, et aucune dépendance supplémentaire.
"""

from __future__ import annotations

from typing import Iterable

_SOF_MARKERS = {
    0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
    0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF,
}
DEFAULT_DPI = 300.0


def jpeg_info(data: bytes) -> tuple[int, int, int, float]:
    """Retourne (largeur, hauteur, composantes, dpi) d'un JPEG."""
    if not data.startswith(b"\xff\xd8"):
        raise ValueError("Ce n'est pas un fichier JPEG")
    dpi = DEFAULT_DPI
    i = 2
    size = len(data)
    while i < size - 1:
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        i += 2
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
            continue
        if marker == 0xD9:
            break
        if i + 2 > size:
            break
        seg_len = int.from_bytes(data[i:i + 2], "big")
        segment = data[i + 2:i + seg_len]
        if marker == 0xE0 and segment[:5] == b"JFIF\x00" and len(segment) >= 12:
            units = segment[7]
            x_density = int.from_bytes(segment[8:10], "big")
            if units == 1 and x_density:          # points par pouce
                dpi = float(x_density)
            elif units == 2 and x_density:        # points par centimètre
                dpi = x_density * 2.54
        if marker in _SOF_MARKERS and len(segment) >= 6:
            height = int.from_bytes(segment[1:3], "big")
            width = int.from_bytes(segment[3:5], "big")
            components = segment[5]
            return width, height, components, dpi
        i += seg_len
    raise ValueError("Dimensions JPEG introuvables")


def jpegs_to_pdf(images: Iterable[bytes]) -> bytes:
    """Assemble des JPEG en un PDF, une image par page."""
    images = list(images)
    if not images:
        raise ValueError("Aucune image à assembler")

    objects: list[bytes] = []

    def add(body: bytes) -> int:
        objects.append(body)
        return len(objects)          # numéro d'objet (1-based)

    catalog_num = add(b"")           # réservé, rempli plus bas
    pages_num = add(b"")
    page_nums: list[int] = []

    for image in images:
        width, height, components, dpi = jpeg_info(image)
        pt_w = width * 72.0 / dpi
        pt_h = height * 72.0 / dpi
        colorspace = b"/DeviceGray" if components == 1 else (
            b"/DeviceCMYK" if components == 4 else b"/DeviceRGB")

        image_num = add(
            b"<< /Type /XObject /Subtype /Image /Width " + str(width).encode()
            + b" /Height " + str(height).encode()
            + b" /ColorSpace " + colorspace
            + b" /BitsPerComponent 8 /Filter /DCTDecode /Length "
            + str(len(image)).encode() + b" >>\nstream\n" + image + b"\nendstream"
        )
        content = (f"q {pt_w:.4f} 0 0 {pt_h:.4f} 0 0 cm /Im0 Do Q\n").encode("ascii")
        content_num = add(
            b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n"
            + content + b"endstream"
        )
        page_num = add(
            b"<< /Type /Page /Parent " + str(pages_num).encode() + b" 0 R"
            + f" /MediaBox [0 0 {pt_w:.4f} {pt_h:.4f}]".encode("ascii")
            + b" /Resources << /XObject << /Im0 " + str(image_num).encode() + b" 0 R >> >>"
            + b" /Contents " + str(content_num).encode() + b" 0 R >>"
        )
        page_nums.append(page_num)

    kids = b" ".join(f"{n} 0 R".encode("ascii") for n in page_nums)
    objects[pages_num - 1] = (
        b"<< /Type /Pages /Kids [" + kids + b"] /Count "
        + str(len(page_nums)).encode() + b" >>"
    )
    objects[catalog_num - 1] = b"<< /Type /Catalog /Pages " + str(pages_num).encode() + b" 0 R >>"

    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets: list[int] = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += str(number).encode() + b" 0 obj\n" + body + b"\nendobj\n"

    xref_at = len(out)
    out += b"xref\n0 " + str(len(objects) + 1).encode() + b"\n"
    out += b"0000000000 65535 f \n"
    for offset in offsets:
        out += f"{offset:010d} 00000 n \n".encode("ascii")
    out += (
        b"trailer\n<< /Size " + str(len(objects) + 1).encode()
        + b" /Root " + str(catalog_num).encode() + b" 0 R >>\nstartxref\n"
        + str(xref_at).encode() + b"\n%%EOF\n"
    )
    return bytes(out)
