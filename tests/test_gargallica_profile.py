import json
from pathlib import Path

from bnf_p0.deploy import apply_profile, git_blob_sha, rollback, verify_profile

ROOT = Path(__file__).parents[1]


def test_gargallica_profile_apply_verify_rollback(tmp_path):
    manifest = json.loads((ROOT / "deployment/upstream_manifest.json").read_text(encoding="utf-8"))
    profile = manifest["profiles"]["gargallica"]

    # Rebuild a minimal checkout containing the exact snippets targeted by the
    # profile. The profile SHA is replaced by the fixture SHA so this test
    # exercises patch semantics independently of GitHub availability.
    target = tmp_path / "gargallica"
    target.mkdir()
    original_gallica = (
        "library(rvest)\n"
        "page <- function(i)xml2::read_xml(paste0('http://gallica.bnf.fr/SRU?operation=searchRetrieve&version=1.2&query=(', question,')&collapsing=false&maximumRecords=50&startRecord=', i))\n"
        "  x %>%\n"
        "    read_html() %>%\n"
        "    html_text()\n"
    ).encode("utf-8")
    original_hd = b"legacy hd\n"
    (target / "gallica.R").write_bytes(original_gallica)
    (target / "full_hd_image.R").write_bytes(original_hd)

    test_profile = json.loads(json.dumps(profile))
    for item in test_profile["files"]:
        if item["path"] == "gallica.R":
            item["expected_blob_sha"] = git_blob_sha(original_gallica)
        elif item["path"] == "full_hd_image.R":
            item["expected_blob_sha"] = git_blob_sha(original_hd)

    apply_profile(target, test_profile, ROOT)

    patched = (target / "gallica.R").read_text(encoding="utf-8")
    assert 'source("gallica_api.R")' in patched
    assert "https://gallica.bnf.fr/SRU" in patched
    assert "gargallica_read_xml" in patched
    assert "gargallica_read_html() %>%" in patched
    assert (target / "gallica_api.R").exists()
    assert "https://gallica.bnf.fr/iiif" in (target / "full_hd_image.R").read_text(encoding="utf-8")

    ok, _, problems = verify_profile(target, test_profile, ROOT)
    assert ok, problems

    rollback(target)
    assert (target / "gallica.R").read_bytes() == original_gallica
    assert (target / "full_hd_image.R").read_bytes() == original_hd
    assert not (target / "gallica_api.R").exists()
