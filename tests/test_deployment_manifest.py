import json
import runpy
from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_manifest_sources_exist_and_profiles_are_complete():
    manifest = json.loads((ROOT / "deployment/upstream_manifest.json").read_text())
    assert manifest["package_version"] == "0.1.3"
    assert set(manifest["profiles"]) == {"pygallica", "pyllica", "gallipy", "gargallica"}
    for profile in manifest["profiles"].values():
        for item in profile["files"]:
            assert len(item["expected_blob_sha"]) == 40
            if item["action"] == "replace":
                assert (ROOT / item["source"]).is_file()


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
