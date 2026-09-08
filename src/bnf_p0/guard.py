"""Contrôle du contenu réellement renvoyé par Gallica.

Gallica sert désormais une page de vérification anti-robot sur ses routes web
(`.texteBrut`, `.pdf`). Elle arrive avec un statut HTTP 200 et du HTML : un
client qui ne regarde que le code de statut l'enregistre comme si c'était le
contenu demandé. Ce module rend cette situation explicite.
"""

from __future__ import annotations

import httpx

_SECURITY_MARKERS = (b"altcha", b"rification de s\xc3\xa9curit\xc3\xa9")

_FAMILIES = {
    "xml": ("application/xml", "text/xml"),
    "json": ("application/json",),
    "image": ("image/",),
    "pdf": ("application/pdf",),
}

_MAGIC = {
    "xml": (b"<?xml", b"<"),
    "json": (b"{", b"["),
    "image": (b"\xff\xd8\xff", b"\x89PNG", b"GIF8", b"II*\x00", b"MM\x00*"),
    "pdf": (b"%PDF",),
}


class GallicaSecurityCheck(RuntimeError):
    """Gallica a renvoyé sa page de vérification à la place du contenu."""


class GallicaUnexpectedContent(RuntimeError):
    """Gallica a répondu 200 avec un type de contenu inattendu."""


def looks_like_security_page(payload: bytes) -> bool:
    head = payload[:200_000].lower()
    return any(marker in head for marker in _SECURITY_MARKERS)


def guard(response: httpx.Response, *, expect: str, url: str | None = None) -> httpx.Response:
    """Vérifie que la réponse est bien du type attendu.

    `expect` vaut "xml", "json", "image" ou "pdf". Un statut 200 accompagné de
    HTML est traité comme un échec, pas comme un succès.
    """
    if expect not in _FAMILIES:
        raise ValueError(f"famille de contenu inconnue: {expect!r}")

    content_type = response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    where = url or str(response.request.url)

    if any(content_type.startswith(prefix) for prefix in _FAMILIES[expect]):
        return response

    if looks_like_security_page(response.content):
        raise GallicaSecurityCheck(
            f"Gallica a renvoyé sa page de vérification anti-robot pour {where} "
            f"(HTTP {response.status_code}, {content_type or 'type inconnu'}). "
            "Cette route est servie par le site web, pas par une API. "
            "Utiliser la route API équivalente (ALTO pour le texte, IIIF pour les images)."
        )

    # Gallica renseigne toujours Content-Type. Son absence signale un transport
    # de test ou un intermédiaire : on se rabat alors sur la signature du
    # contenu, sans transformer cette incertitude en échec.
    if not content_type:
        payload = response.content.lstrip()[:8]
        if not payload or any(payload.startswith(m) for m in _MAGIC[expect]):
            return response
        return response

    if looks_like_security_page(response.content):
        raise GallicaSecurityCheck(
            f"Gallica a renvoyé sa page de vérification anti-robot pour {where} "
            f"(HTTP {response.status_code}, {content_type or 'type inconnu'}). "
            "Cette route est servie par le site web, pas par une API. "
            "Utiliser la route API équivalente (ALTO pour le texte, IIIF pour les images)."
        )

    raise GallicaUnexpectedContent(
        f"Contenu inattendu pour {where}: attendu {expect}, reçu "
        f"{content_type or 'type inconnu'} ({len(response.content)} octets)."
    )
