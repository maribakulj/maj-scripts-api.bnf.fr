import bnf_p0.compat.pygallica as pg


class FakeClient:
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def precalculated_image(self, identifier, resolution): return b"jpeg"
    def iiif_image(self, ark, **kwargs): return b"iiif"
    def alto(self, identifier, page): return b"<alto><page>1</page></alto>"


def test_simple_images_preserves_historical_file_side_effect(monkeypatch, tmp_path):
    monkeypatch.setattr(pg, "GallicaClient", FakeClient)
    monkeypatch.chdir(tmp_path)
    assert pg.Document.simple_images("abc", "highres") is None
    assert (tmp_path / "simple_image.jpg").read_bytes() == b"jpeg"


def test_iiif_preserves_historical_file_side_effect(monkeypatch, tmp_path):
    monkeypatch.setattr(pg, "GallicaClient", FakeClient)
    monkeypatch.chdir(tmp_path)
    assert pg.IIIF.iiif("12148/abc/f1", "full", "1000,", "0", "native", "jpg") is None
    assert (tmp_path / "12148/abc/f1.jpg").read_bytes() == b"iiif"


def test_ocr_returns_structured_mapping(monkeypatch):
    monkeypatch.setattr(pg, "GallicaClient", FakeClient)
    result = pg.Document.ocr("abc", 1)
    assert result["alto"]["page"] == "1"
