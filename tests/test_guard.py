import httpx
import pytest

from bnf_p0.guard import GallicaSecurityCheck, GallicaUnexpectedContent, guard

URL = "https://gallica.bnf.fr/ark:/12148/bpt6kX.pdf"

SECURITY_PAGE = (
    b"<!DOCTYPE html> <html><head><title>Gallica | "
    b"V\xc3\xa9rification de s\xc3\xa9curit\xc3\xa9</title>"
    b"<script>altcha</script></head><body></body></html>"
)


def response(content, content_type=None, status=200):
    headers = {"content-type": content_type} if content_type else {}
    return httpx.Response(status, content=content, headers=headers,
                          request=httpx.Request("GET", URL))


def test_security_page_served_as_200_is_rejected():
    with pytest.raises(GallicaSecurityCheck) as excinfo:
        guard(response(SECURITY_PAGE, "text/html;charset=UTF-8"), expect="pdf")
    assert "anti-robot" in str(excinfo.value)


def test_html_instead_of_pdf_is_rejected_even_without_security_markers():
    with pytest.raises(GallicaUnexpectedContent):
        guard(response(b"<html><body>erreur</body></html>", "text/html"), expect="pdf")


def test_expected_content_passes_through():
    ok = response(b"%PDF-1.4 ...", "application/pdf")
    assert guard(ok, expect="pdf") is ok


def test_charset_suffix_does_not_break_matching():
    ok = response(b"<?xml version='1.0'?><r/>", "application/xml;charset=UTF-8")
    assert guard(ok, expect="xml") is ok


def test_missing_content_type_falls_back_to_signature():
    ok = response(b"<?xml version='1.0'?><r/>")
    assert guard(ok, expect="xml") is ok


def test_missing_content_type_still_catches_the_security_page():
    with pytest.raises(GallicaSecurityCheck):
        guard(response(SECURITY_PAGE), expect="xml")
