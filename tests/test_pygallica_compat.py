from bnf_p0.compat.pygallica import Document


def test_oai_alias_exists():
    assert callable(Document.oai)
    assert callable(Document.OAI)
