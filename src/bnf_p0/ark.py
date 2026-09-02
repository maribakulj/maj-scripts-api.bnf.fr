from __future__ import annotations

import re
from urllib.parse import urlparse

_ARK_RE = re.compile(r"(?:ark:/12148/|(?:^|/)12148/)([A-Za-z0-9]+)", re.IGNORECASE)
_SIMPLE_RE = re.compile(r"^[A-Za-z0-9]+$")


def normalize_ark_id(value: str) -> str:
    """Retourne l'identifiant Gallica nu (ex. bpt6k5738219s)."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Un identifiant ARK non vide est requis")
    raw = value.strip()
    match = _ARK_RE.search(raw)
    if match:
        return match.group(1)
    parsed = urlparse(raw)
    if parsed.scheme and parsed.path:
        match = _ARK_RE.search(parsed.path)
        if match:
            return match.group(1)
    raw = raw.strip("/")
    raw = raw.split("/", 1)[0]
    raw = raw.split(".", 1)[0]
    if _SIMPLE_RE.fullmatch(raw):
        return raw
    raise ValueError(f"Identifiant ARK Gallica non reconnu: {value!r}")


def ark_uri(value: str) -> str:
    return f"ark:/12148/{normalize_ark_id(value)}"


def gallica_url(value: str) -> str:
    return f"https://gallica.bnf.fr/{ark_uri(value)}"
