from pathlib import Path

ROOT = Path(__file__).parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_bnfimage_hd_requests_are_throttled_below_five_per_minute():
    text = read("legacy_replacements/bnfimage/R/utils.R")
    assert 'interval <- if (high_resolution) 12.5 else 3' in text
    assert 'response$status_code != 429' in text
    assert 'retry-after' in text
    assert 'httr::timeout(60)' in text


def test_bnfimage_surfaces_unrecovered_429():
    text = read("legacy_replacements/bnfimage/R/bi_image.R")
    assert 'bi_query$status_code == 429' in text
    assert 'httr::stop_for_status' in text


def test_gargallica_helper_uses_https_and_text_rate_limit():
    text = read("legacy_replacements/gargallica/gallica_api.R")
    assert '12.5' in text
    assert 'rate_class = "texteBrut"' in text
    assert 'response$status_code %in% c(429, 500, 502, 503, 504)' in text
    assert 'httr::timeout(60)' in text


def test_manifest_patches_gargallica_sru_and_raw_text_calls():
    text = read("deployment/upstream_manifest.json")
    assert 'https://gallica.bnf.fr/SRU' in text
    assert 'gargallica_read_html() %>%' in text
    assert '"action": "create"' in text
    assert '"bnfimage"' in text
