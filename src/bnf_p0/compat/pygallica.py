"""Compatibilité avec les exemples historiques PyGallica publiés sur api.bnf.fr."""

from __future__ import annotations

from pathlib import Path

from bnf_p0 import GallicaClient
from bnf_p0.xmlutil import document_to_dict


def _best_effort_markup_dict(value: str):
    try:
        return document_to_dict(value.encode("utf-8"))
    except Exception:
        return value


class Search:
    @staticmethod
    def search(*terms: str):
        if not terms:
            raise ValueError("Au moins un terme est requis")
        query = " and ".join(f'gallica all "{term}"' for term in terms)
        with GallicaClient() as client:
            return client.sru(query)


class Document:
    @staticmethod
    def issues(identifier: str):
        with GallicaClient() as client:
            return client.issues(identifier)

    @staticmethod
    def issues_date(identifier: str, year: str | int):
        with GallicaClient() as client:
            return client.issues(identifier, year=int(year))

    @staticmethod
    def oai(identifier: str):
        with GallicaClient() as client:
            return client.oai_record(identifier)

    OAI = oai

    @staticmethod
    def pagination(identifier: str):
        with GallicaClient() as client:
            return client.pagination(identifier)

    @staticmethod
    def simple_images(identifier: str, resolution: str):
        with GallicaClient() as client:
            data = client.precalculated_image(identifier, resolution=resolution)
        Path("simple_image.jpg").write_bytes(data)
        return None

    @staticmethod
    def content(identifier: str, query: str):
        with GallicaClient() as client:
            return client.content_search(identifier, query)

    @staticmethod
    def content_page(identifier: str, query: str, page: str | int):
        with GallicaClient() as client:
            return client.content_search(identifier, query, page=int(page))

    @staticmethod
    def toc(identifier: str):
        with GallicaClient() as client:
            raw = client.toc(identifier)
        return _best_effort_markup_dict(raw)

    @staticmethod
    def texte_brut(identifier: str):
        with GallicaClient() as client:
            raw = client.texte_brut(identifier)
        return _best_effort_markup_dict(raw)

    @staticmethod
    def ocr(identifier: str, page: str | int):
        with GallicaClient() as client:
            raw = client.alto(identifier, int(page))
        return document_to_dict(raw)


class IIIF:
    @staticmethod
    def iiif(identifier: str, region: str, size: str, rotation, quality: str, format: str):
        raw = identifier.strip("/")
        view = 1
        if "/f" in raw:
            base, qualifier = raw.rsplit("/f", 1)
            if qualifier.isdigit():
                view = int(qualifier)
                raw = base
        with GallicaClient() as client:
            data = client.iiif_image(raw, view=view, region=region, size=size,
                                     rotation=rotation, quality=quality, fmt=format)
        output = Path(f"{identifier}.{format}")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(data)
        return None

    @staticmethod
    def metadata(identifier: str):
        raw = identifier.strip("/")
        view = 1
        if "/f" in raw:
            base, qualifier = raw.rsplit("/f", 1)
            if qualifier.isdigit():
                view = int(qualifier)
                raw = base
        with GallicaClient() as client:
            return client.iiif_info(raw, view=view)
