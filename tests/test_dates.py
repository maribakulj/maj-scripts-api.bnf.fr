from bnf_p0.compat.pyllica import pressdate


def test_gregorian_leap_year_2000():
    assert pressdate(2000, 2, 28, 1, 3) == ["20000228", "20000229", "20000301"]


def test_non_leap_year_1900():
    assert pressdate(1900, 2, 28, 1, 2) == ["19000228", "19000301"]


class _FakeClient:
    def __init__(self): self.calls = []
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def issue_for_date(self, periodical, when): return "bpt6kISSUE"
    def text(self, ark, **kw): self.calls.append(("text", ark)); return "texte océrisé"
    def pdf_from_iiif(self, ark, **kw): self.calls.append(("iiif", ark)); return b"%PDF-1.4 iiif"
    def pdf(self, ark, **kw): self.calls.append(("web", ark)); return b"%PDF-1.4 web"


def test_textpress_reads_the_alto_route(monkeypatch, tmp_path):
    import bnf_p0.compat.pyllica as pl
    fake = _FakeClient()
    monkeypatch.setattr(pl, "GallicaClient", lambda: fake)
    saved = pl.textpress("cb32798952c", title="f", year=1937, month=3, day=25,
                         item=1, output_dir=tmp_path)
    assert [c[0] for c in fake.calls] == ["text"]
    assert saved[0].read_text(encoding="utf-8") == "texte océrisé"


def test_pdfpress_rebuilds_from_iiif_by_default(monkeypatch, tmp_path):
    import bnf_p0.compat.pyllica as pl
    fake = _FakeClient()
    monkeypatch.setattr(pl, "GallicaClient", lambda: fake)
    saved = pl.pdfpress("cb32798952c", title="f", year=1937, month=3, day=25,
                        item=1, output_dir=tmp_path)
    assert [c[0] for c in fake.calls] == ["iiif"]
    assert saved[0].read_bytes().startswith(b"%PDF")


def test_pdfpress_can_still_ask_for_the_historical_route(monkeypatch, tmp_path):
    import bnf_p0.compat.pyllica as pl
    fake = _FakeClient()
    monkeypatch.setattr(pl, "GallicaClient", lambda: fake)
    pl.pdfpress("cb32798952c", title="f", year=1937, month=3, day=25, item=1,
                output_dir=tmp_path, source="web")
    assert [c[0] for c in fake.calls] == ["web"]


def test_pdfpress_refuses_an_unknown_source():
    import bnf_p0.compat.pyllica as pl
    import pytest
    with pytest.raises(ValueError):
        pl.pdfpress("cb32798952c", source="ftp")
