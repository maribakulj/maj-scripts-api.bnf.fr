"""Lecture des fichiers ALTO servis par Gallica.

Deux particularités sont traitées ici :

1. Gallica déclare `encoding="ISO-8859-1"` dans ses ALTO alors que les octets
   sont de l'UTF-8 (l'en-tête HTTP annonce d'ailleurs `charset=UTF-8`). Un
   analyseur XML conforme suit la déclaration du fichier et abîme tous les
   accents. On corrige la déclaration avant l'analyse.
2. L'ALTO est la seule route API donnant le texte océrisé : elle remplace
   `.texteBrut`, qui est une URL du site web désormais protégée.
"""

from __future__ import annotations

import re
from xml.etree import ElementTree as ET

from .xmlutil import local_name

_DECL_RE = re.compile(rb'^(<\?xml[^>]*encoding=")([^"]+)(")', re.IGNORECASE)


def decode_alto(data: bytes) -> str:
    """Décode un ALTO Gallica en corrigeant sa déclaration d'encodage."""
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("latin-1")
    return _DECL_RE.sub(lambda m: m.group(1) + b"UTF-8" + m.group(3), data, count=1).decode("utf-8")


def parse_alto(data: bytes) -> ET.Element:
    return ET.fromstring(decode_alto(data))


def alto_to_text(data: bytes) -> str:
    """Recompose le texte d'une page ALTO, dans l'ordre de lecture."""
    root = parse_alto(data)
    blocks: list[str] = []
    for block in root.iter():
        if local_name(block.tag) != "TextBlock":
            continue
        lines: list[str] = []
        for line in block:
            if local_name(line.tag) != "TextLine":
                continue
            words: list[str] = []
            hyphenated = False
            for element in line:
                name = local_name(element.tag)
                if name == "String":
                    content = element.attrib.get("CONTENT", "")
                    if content:
                        words.append(content)
                elif name == "HYP":
                    hyphenated = True
            if words:
                lines.append(" ".join(words) + ("­" if hyphenated else ""))
        if lines:
            blocks.append("\n".join(lines))
    return "\n\n".join(blocks)
