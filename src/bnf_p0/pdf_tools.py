from __future__ import annotations

import io
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from .client import GallicaClient


def download_pdf(ark: str, output: str | Path, *, start: int = 1, end: int | None = None,
                 block_size: int = 100, client: GallicaClient | None = None) -> Path:
    """Remplacement du getpdf Gallipy sans fallback arbitraire à 1000 vues."""
    owns_client = client is None
    client = client or GallicaClient()
    try:
        nviews = client.view_count(ark)
        start = max(1, min(int(start), nviews))
        end = nviews if end is None else max(start, min(int(end), nviews))
        block_size = max(1, int(block_size))

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
