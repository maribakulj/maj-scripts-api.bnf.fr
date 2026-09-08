import json
import runpy
from importlib.metadata import version
from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_manifest_sources_exist_and_profiles_are_complete():
    manifest = json.loads((ROOT / "deployment/upstream_manifest.json").read_text())
    assert manifest["package_version"] == version("bnf-api-p0")
    assert set(manifest["profiles"]) == {"pygallica", "pyllica", "gallipy", "gargallica", "bnfimage"}
    for profile in manifest["profiles"].values():
        for item in profile["files"]:
            if item["action"] == "create":
                assert "expected_blob_sha" not in item
            else:
                assert len(item["expected_blob_sha"]) == 40
            if item["action"] in {"replace", "create"}:
                assert (ROOT / item["source"]).is_file()
            elif item["action"] == "text_patch":
                assert item["patches"]
            else:
                raise AssertionError(f"action inconnue: {item['action']}")


def test_vendored_pygallica_wrapper_imports_after_deployment(tmp_path):
    from bnf_p0.deploy import apply_profile, git_blob_sha

    target = tmp_path / "repo"
    (target / "python3").mkdir(parents=True)
    old = b"# old wrapper\n"
    (target / "python3/search_api.py").write_bytes(old)
    profile = {
        "repository": "example/PyGallica",
        "vendor_core": True,
        "files": [{
            "path": "python3/search_api.py",
            "expected_blob_sha": git_blob_sha(old),
            "action": "replace",
            "source": "legacy_replacements/PyGallica/python3/search_api.py",
        }],
    }
    apply_profile(target, profile, ROOT)
    module = runpy.run_path(str(target / "python3/search_api.py"))
    assert "Search" in module


def test_gallipy_sets_a_user_agent_on_its_only_network_call():
    """Gallica renvoie 403 à l'agent par défaut d'urllib. Les dix fonctions
    synchrones de gallipy passent toutes par `helpers.py`, donc aucune ne
    fonctionne tant que cette requête n'annonce pas de User-Agent."""
    import json
    from pathlib import Path

    manifest = json.loads((Path(__file__).parents[1] / "deployment" / "upstream_manifest.json").read_text(encoding="utf-8"))
    helpers = [f for f in manifest["profiles"]["gallipy"]["files"] if f["path"] == "gallipy/helpers.py"]
    assert helpers, "le profil gallipy doit corriger helpers.py"
    patch = helpers[0]["patches"][0]
    assert "urlopen(url" in patch["old"]
    assert "User-Agent" in patch["new"]
    assert "urlopen(request" in patch["new"]
