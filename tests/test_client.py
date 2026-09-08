from datetime import date
from pathlib import Path
import httpx

from bnf_p0.client import GallicaClient
from bnf_p0.http import RobustHttpClient
from bnf_p0.rate_limit import RateLimiter

FIX = Path(__file__).parent / "fixtures"


def make_client(handler):
    http = RobustHttpClient(
        transport=httpx.MockTransport(handler),
        limiter=RateLimiter(intervals={"default": 0, "text": 0, "pdf": 0, "iiif_hd": 0, "highres": 0}),
        sleeper=lambda _: None,
    )
    return GallicaClient(http)


def test_view_count_uses_nbVueImages_without_fallback():
    data = (FIX / "pagination.xml").read_bytes()
    def handler(request): return httpx.Response(200, content=data, request=request, headers={"content-type": "application/xml;charset=UTF-8"})
    with make_client(handler) as client:
        assert client.view_count("bpt6k5738219s") == 374


def test_issue_resolution_uses_issues_api():
    data = (FIX / "issues.xml").read_bytes()
    seen = []
    def handler(request):
        seen.append(str(request.url))
        return httpx.Response(200, content=data, request=request, headers={"content-type": "application/xml;charset=UTF-8"})
    with make_client(handler) as client:
        assert client.issue_for_date("cb32798952c", date(1937, 3, 25)) == "bpt6k5509212w"
    assert "/services/Issues" in seen[0]
    assert "date=1937" in seen[0]


def test_iiif_hd_selects_hd_bucket_and_url():
    seen = []
    def handler(request):
        seen.append(str(request.url))
        return httpx.Response(200, content=b"jpg", request=request, headers={"content-type": "image/jpeg"})
    with make_client(handler) as client:
        assert client.iiif_image("btv1b53066668g", view=1, size="3000,", fmt="jpg") == b"jpg"
    assert seen[0].startswith("https://gallica.bnf.fr/iiif/ark:/12148/btv1b53066668g/f1/full/3000,")


def test_issue_resolution_uses_structured_day_of_year_not_free_text():
    data = (FIX / "issues.xml").read_bytes()
    def handler(request):
        return httpx.Response(200, content=data, request=request, headers={"content-type": "application/xml;charset=UTF-8"})
    with make_client(handler) as client:
        assert client.issue_for_date("cb32798952c", date(1937, 3, 18)) == "bpt6k5505325m"
        assert client.issue_for_date("cb32798952c", date(1937, 3, 25)) == "bpt6k5509212w"


def test_content_search_supports_start_result():
    seen = []
    def handler(request):
        seen.append(str(request.url))
        return httpx.Response(200, content=b"<results/>", request=request)
    with make_client(handler) as client:
        client.content_search("bpt6k5460422k", "hugo", start_result=11)
    assert "startResult=11" in seen[0]


def test_text_warns_loudly_when_the_document_is_long(caplog):
    """`.texteBrut` livrait un document en un appel ; l'ALTO est paginé. Sur un
    livre, l'attente se compte en dizaines de minutes : il faut le dire avant."""
    import logging
    data = (FIX / "pagination.xml").read_bytes()   # 374 vues

    def handler(request):
        if "Pagination" in str(request.url):
            return httpx.Response(200, content=data, request=request,
                                  headers={"content-type": "application/xml"})
        return httpx.Response(200, content=b"<alto/>", request=request,
                              headers={"content-type": "application/xml"})

    # Le limiteur garde sa cadence réelle pour que l'estimation soit vraie,
    # mais n'attend pas : c'est le message qu'on teste, pas la temporisation.
    http = RobustHttpClient(
        transport=httpx.MockTransport(handler),
        limiter=RateLimiter(intervals={"default": 0, "alto": 12.25},
                            sleeper=lambda _: None),
        sleeper=lambda _: None,
    )
    with caplog.at_level(logging.WARNING, logger="bnf_p0.client"):
        with GallicaClient(http) as client:
            client.text("bpt6kX", nviews=20)
    messages = [r.getMessage() for r in caplog.records]
    assert any("min" in m for m in messages), messages
    assert any("20 vue" in m for m in messages), messages


def test_text_stays_quiet_for_a_single_page():
    import logging
    data = (FIX / "pagination.xml").read_bytes()

    def handler(request):
        if "Pagination" in str(request.url):
            return httpx.Response(200, content=data, request=request,
                                  headers={"content-type": "application/xml"})
        return httpx.Response(200, content=b"<alto/>", request=request,
                              headers={"content-type": "application/xml"})

    with make_client(handler) as client:
        assert client.text("bpt6kX", nviews=1) == ""
