import ast
import json
import re
from pathlib import Path

ROOT = Path(__file__).parents[1]
DOCS = ROOT / "docs" / "api.bnf.fr"


def read(name: str) -> str:
    return (DOCS / name).read_text(encoding="utf-8")


def python_blocks(markdown: str):
    return re.findall(r"```python\n(.*?)```", markdown, flags=re.DOTALL)


def test_all_python_examples_are_syntactically_valid():
    for page in ["wrappers-gallica.md", "pyllica.md"]:
        for block in python_blocks(read(page)):
            ast.parse(block)


def test_wrappers_page_marks_pygallica_historical_and_fdh_unverified():
    text = read("wrappers-gallica.md")
    assert "dépôt d’origine est archivé" in text
    assert "ressource historique à vérifier" in text
    assert "ne vaut ni garantie de maintenance ni support institutionnel" in text


def test_wrappers_iiif_example_uses_safe_default_and_quota_warning():
    text = read("wrappers-gallica.md")
    assert '"full", "1000", "0"' in text
    assert "5 appels par minute" in text
    assert "IIIF.iiif(" in text


def test_pyllica_high_resolution_examples_are_explicitly_throttled():
    text = read("pyllica.md")
    assert "full/1000/0/native.jpg" in text
    assert "full/3000/0/native.jpg" in text
    assert "à utiliser avec throttling" in text
    assert "5 appels par minute" in text
    assert "dayOfYear" in text


def test_iiif_page_does_not_claim_public_v3():
    text = read("iiif-gallica.md")
    assert "Version 2" in text
    assert "5 appels/minute" in text
    forbidden = ["API publique est en version 3", "Version actuellement documentée : 3"]
    assert not any(term in text for term in forbidden)


def test_status_matrix_is_conservative():
    data = json.loads(read("wrapper-status.json"))
    wrappers = {item["name"]: item for item in data["wrappers"]}
    assert wrappers["PyGallica"]["github_archived"] is True
    assert wrappers["PyGallica"]["editorial_status"] == "historical"
    assert wrappers["fdh-gallica"]["editorial_status"] == "unverified-link"
    for name in ["Gallipy", "Pyllica", "bnfimage", "gargallica"]:
        assert wrappers[name]["github_archived"] is False
        assert wrappers[name]["editorial_status"] == "third-party-audited"


def test_no_deprecated_gallicalabs_http_endpoint_in_proposed_pages():
    for path in DOCS.glob("*.md"):
        text = path.read_text(encoding="utf-8")
        assert "http://gallicalabs.bnf.fr" not in text
