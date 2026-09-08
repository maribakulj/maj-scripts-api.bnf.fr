from __future__ import annotations

import io
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from .client import GallicaClient


def download_pdf(ark: str, output: str | Path, *, start: int = 1, end: int | None = None,
                 block_size: int = 100, client: GallicaClient | None = None,
                 source: str = "iiif", width: int = 1000) -> Path:
    """Remplacement du getpdf Gallipy sans fallback arbitraire à 1000 vues.

    `source="iiif"` (défaut) reconstruit le PDF à partir des images IIIF : le
    suffixe `.pdf` est une URL du site web, désormais derrière une vérification
    anti-robot, et aucune route API ne produit le PDF de Gallica. Le résultat
    est donc fait d'images, sans couche de texte.

    `source="web"` conserve la route historique et son assemblage par blocs ;
    elle refonctionnera si Gallica la rouvre.
    """
    if source not in {"iiif", "web"}:
        raise ValueError("source doit valoir 'iiif' ou 'web'")
    owns_client = client is None
    client = client or GallicaClient()
    try:
        nviews = client.view_count(ark)
        start = max(1, min(int(start), nviews))
        end = nviews if end is None else max(start, min(int(end), nviews))
        block_size = max(1, int(block_size))

        if source == "iiif":
            data = client.pdf_from_iiif(ark, start_view=start,
                                        nviews=end - start + 1, width=width)
            output = Path(output)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(data)
            return output

        writer = PdfWriter()
        current = start
        block_index = 0
        while current <= end:
            count = min(block_size, end - current + 1)
            data = client.pdf(ark, start_view=current, nviews=count)
            reader = PdfReader(io.BytesIO(data))
            # Gallica ajoute historiquement deux pages de garde aux PDF partiels.
            # On les conserve sur le premier bloc et on les retire sur les suivants,
            # comme le faisait le script Gallipy original.
            pages = reader.pages if block_index == 0 else reader.pages[2:]
            for page in pages:
                writer.add_page(page)
            current += count
            block_index += 1

        output = Path(output)
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("wb") as fh:
            writer.write(fh)
        return output
    finally:
        if owns_client:
            client.close()
