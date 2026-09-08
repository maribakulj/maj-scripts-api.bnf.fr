from __future__ import annotations

import logging
import re
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import quote

from .alto import alto_to_text
from .ark import ark_uri, gallica_url, normalize_ark_id
from .guard import GallicaSecurityCheck, guard, looks_like_security_page
from .http import RobustHttpClient
from .pdf_build import jpegs_to_pdf
from .xmlutil import document_to_dict, find_first_text, local_name, parse_xml

log = logging.getLogger(__name__)

BASE = "https://gallica.bnf.fr"


class GallicaClient:
    def __init__(self, http: RobustHttpClient | None = None) -> None:
        self.http = http or RobustHttpClient()
        self._issues_cache: dict[tuple[str, int], dict[str, str]] = {}

    def close(self) -> None:
        self.http.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    def sru(self, query: str, *, start_record: int = 1, maximum_records: int = 50) -> dict:
        params = {"operation": "searchRetrieve", "version": "1.2", "query": query, "startRecord": str(start_record), "maximumRecords": str(maximum_records)}
        r = guard(self.http.get(f"{BASE}/SRU", params=params), expect="xml")
        return document_to_dict(r.content)

    def oai_record(self, ark: str) -> dict:
        r = guard(self.http.get(f"{BASE}/services/OAIRecord", params={"ark": normalize_ark_id(ark)}), expect="xml")
        return document_to_dict(r.content)

    def pagination(self, ark: str) -> dict:
        r = guard(self.http.get(f"{BASE}/services/Pagination", params={"ark": normalize_ark_id(ark)}), expect="xml")
        return document_to_dict(r.content)

    def view_count(self, ark: str) -> int:
        r = guard(self.http.get(f"{BASE}/services/Pagination", params={"ark": normalize_ark_id(ark)}), expect="xml")
        root = parse_xml(r.content)
        value = find_first_text(root, "nbVueImages")
        if value is None:
            raise ValueError("La réponse Pagination ne contient pas nbVueImages")
        count = int(value)
        if count <= 0:
            raise ValueError(f"Nombre de vues invalide: {count}")
        return count

    def issues(self, periodical: str, *, year: int | None = None) -> dict:
        identifier = normalize_ark_id(periodical)
        params = {"ark": f"ark:/12148/{identifier}/date"}
        if year is not None:
            params["date"] = str(year)
        r = self.http.get(f"{BASE}/services/Issues", params=params)
        return document_to_dict(r.content)

    def _issue_index_for_year(self, periodical: str, year: int) -> dict[str, str]:
        identifier = normalize_ark_id(periodical)
        key = (identifier, year)
        if key in self._issues_cache:
            return self._issues_cache[key]
        params = {"ark": f"ark:/12148/{identifier}/date", "date": str(year)}
        r = self.http.get(f"{BASE}/services/Issues", params=params)
        root = parse_xml(r.content)
        index: dict[str, str] = {}
        for elem in root.iter():
            if local_name(elem.tag) != "issue":
                continue
            ark = elem.attrib.get("ark")
            day_raw = elem.attrib.get("dayOfYear")
            if not ark or not day_raw:
                continue
            try:
                day_of_year = int(day_raw)
                if day_of_year < 1 or day_of_year > 366:
                    continue
                issue_date = date(year, 1, 1) + timedelta(days=day_of_year - 1)
                if issue_date.year != year:
                    continue
            except (TypeError, ValueError, OverflowError):
                continue
            index[issue_date.strftime("%Y%m%d")] = ark
        self._issues_cache[key] = index
        return index

    def issue_for_date(self, periodical: str, when: date) -> str | None:
        return self._issue_index_for_year(periodical, when.year).get(when.strftime("%Y%m%d"))

    def content_search(self, ark: str, query: str, *, page: int | None = None, start_result: int | None = None) -> dict:
        params = {"ark": normalize_ark_id(ark), "query": query}
        if page is not None:
            params["page"] = str(page)
        if start_result is not None:
            if int(start_result) < 1:
                raise ValueError("start_result doit être >= 1")
            params["startResult"] = str(int(start_result))
        r = guard(self.http.get(f"{BASE}/services/ContentSearch", params=params), expect="xml")
        return document_to_dict(r.content)

    def toc(self, ark: str) -> str:
        r = self.http.get(f"{BASE}/services/Toc", params={"ark": ark_uri(ark)})
        return r.text

    def texte_brut(self, ark: str, *, start_view: int | None = None, nviews: int | None = None) -> str:
        root = gallica_url(ark)
        if start_view is None:
            url = f"{root}.texteBrut"
        else:
            if not nviews or nviews < 1:
                raise ValueError("nviews doit être >= 1 lorsque start_view est fourni")
            url = f"{root}/f{int(start_view)}n{int(nviews)}.texteBrut"
        response = self.http.get(url, bucket="text")
        if looks_like_security_page(response.content):
            raise GallicaSecurityCheck(
                f"Gallica a renvoyé sa page de vérification anti-robot pour {url}. "
                "`.texteBrut` est une URL du site web, pas une API : utiliser "
                "GallicaClient.text() ou page_text(), qui passent par l'ALTO."
            )
        return response.text

    def alto(self, ark: str, view: int) -> bytes:
        params = {"O": normalize_ark_id(ark), "E": "ALTO", "Deb": str(int(view))}
        r = guard(self.http.get(f"{BASE}/RequestDigitalElement", params=params, bucket="alto"), expect="xml")
        return r.content

    def precalculated_image(self, ark: str, *, view: int | None = None, resolution: str = "highres") -> bytes:
        if resolution not in {"thumbnail", "lowres", "medres", "highres"}:
            raise ValueError("resolution invalide")
        root = gallica_url(ark)
        url = f"{root}/f{int(view)}.{resolution}" if view else f"{root}/{resolution}"
        bucket = "highres" if resolution == "highres" else "default"
        return guard(self.http.get(url, bucket=bucket), expect="image").content

    @staticmethod
    def _iiif_bucket(size: str) -> str:
        if size == "full":
            return "iiif_hd"
        token = size.split(",", 1)[0].lstrip("!^")
        try:
            if int(token) > 1000:
                return "iiif_hd"
        except ValueError:
            pass
        return "default"

    def iiif_info(self, ark: str, *, view: int = 1) -> dict:
        url = f"{BASE}/iiif/{ark_uri(ark)}/f{int(view)}/info.json"
        return guard(self.http.get(url), expect="json").json()

    def iiif_image(self, ark: str, *, view: int = 1, region: str = "full", size: str = "1000,", rotation: str | int = 0, quality: str = "native", fmt: str = "jpg") -> bytes:
        if not re.fullmatch(r"[A-Za-z0-9]+", fmt):
            raise ValueError("format IIIF invalide")
        url = f"{BASE}/iiif/{ark_uri(ark)}/f{int(view)}/{quote(str(region), safe=',')}/{quote(str(size), safe=',!^')}/{rotation}/{quality}.{fmt}"
        return guard(self.http.get(url, bucket=self._iiif_bucket(str(size))), expect="image").content

    def pdf(self, ark: str, *, start_view: int | None = None, nviews: int | None = None) -> bytes:
        root = gallica_url(ark)
        if start_view is None:
            url = f"{root}.pdf"
        else:
            if not nviews or nviews < 1:
                raise ValueError("nviews doit être >= 1 lorsque start_view est fourni")
            url = f"{root}/f{int(start_view)}n{int(nviews)}.pdf"
        return guard(self.http.get(url, bucket="pdf"), expect="pdf", url=url).content

    # ------------------------------------------------------------------
    # Routes de remplacement, entièrement dans les API
    # ------------------------------------------------------------------

    def page_text(self, ark: str, view: int) -> str:
        """Texte océrisé d'une vue, via l'ALTO (remplace `.texteBrut`)."""
        return alto_to_text(self.alto(ark, view))

    def text(self, ark: str, *, start_view: int = 1, nviews: int | None = None,
             separator: str = "\n\n") -> str:
        """Texte océrisé d'un document, page par page, via l'ALTO.

        Contrairement à `.texteBrut`, cette route n'est pas servie par le site
        web : elle ne rencontre pas la vérification anti-robot.
        """
        total = self.view_count(ark)
        start = max(1, min(int(start_view), total))
        last = total if nviews is None else min(total, start + int(nviews) - 1)
        pages = last - start + 1
        if pages > 1:
            # `.texteBrut` livrait tout le document en un appel ; l'ALTO est
            # paginé. Le coût en requêtes est donc proportionnel au nombre de
            # vues, et l'appelant doit pouvoir l'anticiper.
            log.info("Texte via ALTO : %d vue(s), soit autant de requêtes.", pages)
        return separator.join(self.page_text(ark, view) for view in range(start, last + 1))

    def pdf_from_iiif(self, ark: str, *, start_view: int = 1, nviews: int | None = None,
                      width: int = 1000) -> bytes:
        """Reconstruit un PDF à partir des images IIIF (remplace `.pdf`).

        Les JPEG sont insérés sans recompression. La largeur par défaut est
        volontairement de 1000 pixels : au-delà, les requêtes IIIF relèvent de
        la classe limitée à 5 appels par minute, ce qui rend la reconstruction
        d'un document de plusieurs dizaines de pages très longue.
        """
        total = self.view_count(ark)
        start = max(1, min(int(start_view), total))
        last = total if nviews is None else min(total, start + int(nviews) - 1)
        images = [
            self.iiif_image(ark, view=view, size=f"{int(width)},", fmt="jpg")
            for view in range(start, last + 1)
        ]
        return jpegs_to_pdf(images)

    @staticmethod
    def save(data: bytes | str, path: str | Path) -> Path:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(data, str):
            p.write_text(data, encoding="utf-8")
        else:
            p.write_bytes(data)
        return p
