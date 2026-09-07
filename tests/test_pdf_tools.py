import io
from pathlib import Path

import pytest
from pypdf import PdfReader, PdfWriter
from bnf_p0.pdf_tools import download_pdf


def make_pdf(n):
    out = io.BytesIO()
    w = PdfWriter()
    for _ in range(n):
        w.add_blank_page(width=10, height=10)
    w.write(out)
    return out.getvalue()


class FakeClient:
    def __init__(self): self.calls = []
    def view_count(self, ark): return 4
    def pdf(self, ark, start_view=None, nviews=None):
        self.calls.append((start_view, nviews))
        return make_pdf(4)


def test_block_pdf_drops_repeated_cover_pages(tmp_path):
    client = FakeClient()
    out = download_pdf("bpt6kX", tmp_path / "out.pdf", start=1, end=4, block_size=2, client=client)
    reader = PdfReader(out)
    assert len(reader.pages) == 6
    assert client.calls == [(1, 2), (3, 2)]


def _pdf_serving_client(payload, content_type="application/pdf"):
    """Client réel branché sur un transport qui sert un PDF, comme Gallica
    le fait lorsque la route n'est pas soumise à la vérification anti-robot."""
    import httpx
    from bnf_p0.client import GallicaClient
    from bnf_p0.http import RobustHttpClient
    from bnf_p0.rate_limit import RateLimiter

    seen = []

    def handler(request):
        seen.append(str(request.url))
        body = (FIX_PAGINATION if "Pagination" in str(request.url) else payload)
        ctype = ("application/xml" if "Pagination" in str(request.url) else content_type)
        return httpx.Response(200, content=body, request=request,
                              headers={"content-type": ctype})

    http = RobustHttpClient(
        transport=httpx.MockTransport(handler),
        limiter=RateLimiter(intervals={"default": 0, "pdf": 0}),
        sleeper=lambda _: None,
    )
    return GallicaClient(http), seen


FIX_PAGINATION = (Path(__file__).parent / "fixtures" / "pagination.xml").read_bytes()


def test_historical_pdf_route_still_works_when_gallica_serves_a_pdf():
    """Le garde-fou ne retire pas la route `.pdf` : il rejette seulement ce
    qui n'est pas un PDF. Si Gallica répond normalement, rien ne change."""
    real = make_pdf(3)
    client, seen = _pdf_serving_client(real)
    with client:
        assert client.pdf("bpt6kX", start_view=1, nviews=3) == real
    assert seen[0].endswith("/f1n3.pdf")


def test_download_pdf_still_assembles_blocks_through_the_real_client():
    client, seen = _pdf_serving_client(make_pdf(4))
    with client:
        out = download_pdf("bpt6kX", Path("/tmp/bnf-p0-historique.pdf"),
                           start=1, end=4, block_size=2, client=client)
    assert len(PdfReader(out).pages) == 6
    assert [u for u in seen if ".pdf" in u] == [
        "https://gallica.bnf.fr/ark:/12148/bpt6kX/f1n2.pdf",
        "https://gallica.bnf.fr/ark:/12148/bpt6kX/f3n2.pdf",
    ]


def test_security_page_on_the_pdf_route_is_refused_not_saved():
    from bnf_p0.guard import GallicaSecurityCheck
    page = b"<!DOCTYPE html><html><body>altcha</body></html>"
    client, _ = _pdf_serving_client(page, content_type="text/html;charset=UTF-8")
    with client:
        with pytest.raises(GallicaSecurityCheck):
            client.pdf("bpt6kX", start_view=1, nviews=1)
