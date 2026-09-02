from bnf_p0.ark import normalize_ark_id, ark_uri, gallica_url


def test_normalize_ark_variants():
    expected = "bpt6k5738219s"
    values = [
        expected,
        "ark:/12148/bpt6k5738219s",
        "https://gallica.bnf.fr/ark:/12148/bpt6k5738219s",
        "https://gallica.bnf.fr/ark:/12148/bpt6k5738219s/f12",
        "/12148/bpt6k5738219s/",
        "12148/bpt6k5738219s/f1",
    ]
    assert all(normalize_ark_id(v) == expected for v in values)
    assert ark_uri(expected) == "ark:/12148/bpt6k5738219s"
    assert gallica_url(expected).startswith("https://gallica.bnf.fr/ark:/12148/")
