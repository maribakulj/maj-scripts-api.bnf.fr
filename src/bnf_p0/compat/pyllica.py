from __future__ import annotations

import logging
from datetime import date, timedelta
from html.parser import HTMLParser
from pathlib import Path

from bnf_p0 import GallicaClient, normalize_ark_id

log = logging.getLogger(__name__)


class _TextExtractor(HTMLParser):
    BREAK_TAGS = {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() in self.BREAK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag.lower() in self.BREAK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data):
        self.parts.append(data)

    def text(self) -> str:
        lines = [" ".join(line.split()) for line in "".join(self.parts).splitlines()]
        return "\n".join(line for line in lines if line).strip() + "\n"


def html_to_text(value: str) -> str:
    if "<" not in value or ">" not in value:
        return value
    parser = _TextExtractor()
    parser.feed(value)
    return parser.text()


def pressdate(year: int, month: int, day: int, rate: int, item: int) -> list[str]:
    if item < 1:
        return []
    if rate < 1:
        raise ValueError("rate doit être >= 1")
    start = date(int(year), int(month), int(day))
    return [(start + timedelta(days=rate * i)).strftime("%Y%m%d") for i in range(item)]


def _dates(year, month, day, rate, item):
    start = date(int(year), int(month), int(day))
    for i in range(int(item)):
        yield start + timedelta(days=int(rate) * i)


def _periodical_id(url_or_ark: str) -> str:
    return normalize_ark_id(url_or_ark)


def textpress(url: str, title="titre", year=1900, month=1, day=1, item=5, rate=1,
              lastpage=1, output_dir="."):
    """Extrait le texte de fascicules de périodique.

    Le texte provient de l'ALTO et non de `.texteBrut` : cette dernière est
    une URL du site web, désormais derrière une vérification anti-robot. Le
    contenu est le même OCR, et l'ALTO préserve en plus la structure des
    lignes et des blocs.
    """
    del lastpage
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    periodical = _periodical_id(url)
    saved = []
    with GallicaClient() as client:
        for d in _dates(year, month, day, rate, item):
            ark = client.issue_for_date(periodical, d)
            if not ark:
                log.warning("Aucun fascicule trouvé pour %s", d.isoformat())
                continue
            path = out / f"{title}_{d:%Y%m%d}.txt"
            path.write_text(client.text(ark), encoding="utf-8")
            saved.append(path)
    return saved


def pdfpress(url: str, title="titre", year=1900, month=1, day=1, item=5, rate=1,
             output_dir=".", *, source="iiif", width=1000):
    """Récupère les fascicules en PDF.

    `source="iiif"` (défaut) reconstruit le PDF à partir des images IIIF. Il
    n'existe aucune route API produisant le PDF de Gallica : le suffixe `.pdf`
    est une URL du site web, désormais derrière une vérification anti-robot.
    Le PDF obtenu est donc fait d'images et n'a pas de couche de texte.

    `source="web"` conserve la route historique, qui refonctionnera si Gallica
    la rouvre ; elle lève une erreur explicite tant que ce n'est pas le cas.
    """
    if source not in {"iiif", "web"}:
        raise ValueError("source doit valoir 'iiif' ou 'web'")
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    periodical = _periodical_id(url)
    saved = []
    if source == "iiif":
        log.warning(
            "PDF reconstruit à partir des images IIIF : pas de couche de texte. "
            "Utiliser textpress() pour le texte."
        )
    with GallicaClient() as client:
        for d in _dates(year, month, day, rate, item):
            ark = client.issue_for_date(periodical, d)
            if not ark:
                log.warning("Aucun fascicule trouvé pour %s", d.isoformat())
                continue
            data = (client.pdf_from_iiif(ark, width=width) if source == "iiif"
                    else client.pdf(ark))
            path = out / f"{title}_{d:%Y%m%d}.pdf"
            path.write_bytes(data)
            saved.append(path)
    return saved


def jpg(identifier: str, title="titre", firstpage=1, lastpage=1, *, width=1000,
        fmt="jpg", output_dir="."):
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    saved = []
    size = "full" if width is None else f"{int(width)},"
    with GallicaClient() as client:
        for page in range(int(firstpage), int(lastpage) + 1):
            data = client.iiif_image(identifier, view=page, size=size, fmt=fmt)
            path = out / f"{title}_{page}.{fmt}"
            path.write_bytes(data)
            saved.append(path)
    return saved


def jpgpress(url: str, title="titre", year=1900, month=1, day=1, item=5, rate=1,
             firstpage=1, lastpage=1, *, width=1000, fmt="jpg", output_dir="."):
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    periodical = _periodical_id(url)
    saved = []
    size = "full" if width is None else f"{int(width)},"
    with GallicaClient() as client:
        for d in _dates(year, month, day, rate, item):
            ark = client.issue_for_date(periodical, d)
            if not ark:
                log.warning("Aucun fascicule trouvé pour %s", d.isoformat())
                continue
            for page in range(int(firstpage), int(lastpage) + 1):
                try:
                    data = client.iiif_image(ark, view=page, size=size, fmt=fmt)
                except Exception as exc:
                    log.warning("%s page %s ignorée: %s", d.isoformat(), page, exc)
                    continue
                path = out / f"{title}_{d:%Y%m%d}_{page}.{fmt}"
                path.write_bytes(data)
                saved.append(path)
    return saved
