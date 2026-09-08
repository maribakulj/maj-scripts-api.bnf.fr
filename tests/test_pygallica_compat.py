from bnf_p0.compat.pygallica import Document


def test_oai_alias_exists():
    assert callable(Document.oai)
    assert callable(Document.OAI)


class _AltoClient:
    """Client factice : l'ALTO répond, la route web lève comme en production."""
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def text(self, ark, **kw): return f"texte de {ark}"
    def texte_brut(self, *a, **kw):
        from bnf_p0.guard import GallicaSecurityCheck
        raise GallicaSecurityCheck("page de vérification")


def test_texte_brut_reads_the_alto_route_not_the_web_page(monkeypatch):
    import bnf_p0.compat.pygallica as pg
    monkeypatch.setattr(pg, "GallicaClient", _AltoClient)
    assert pg.Document.texte_brut("bpt6kX") == "texte de bpt6kX"
