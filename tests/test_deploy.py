from pathlib import Path

import pytest

from bnf_p0.deploy import apply_profile, git_blob_sha, rollback, verify_profile


def profile_for(path: str, expected: str, source: str, *, vendor_core=False, action="replace", patches=None):
    item = {"path": path, "expected_blob_sha": expected, "action": action}
    if source:
        item["source"] = source
    if patches:
        item["patches"] = patches
    return {"repository": "example/repo", "vendor_core": vendor_core, "files": [item]}


def test_replace_verify_and_rollback(tmp_path):
    package = tmp_path / "package"
    target = tmp_path / "target"
    (package / "repl").mkdir(parents=True)
    target.mkdir()
    old = b"old\n"
    (target / "a.py").write_bytes(old)
    (package / "repl/a.py").write_bytes(b"new\n")
    profile = profile_for("a.py", git_blob_sha(old), "repl/a.py")

    apply_profile(target, profile, package)
    assert (target / "a.py").read_bytes() == b"new\n"
    ok, _, problems = verify_profile(target, profile, package)
    assert ok and not problems

    rollback(target)
    assert (target / "a.py").read_bytes() == old
    assert not (target / ".bnf-p0-state.json").exists()


def test_drift_refuses_without_force(tmp_path):
    package = tmp_path / "package"
    target = tmp_path / "target"
    (package / "repl").mkdir(parents=True)
    target.mkdir()
    (target / "a.py").write_text("changed\n")
    (package / "repl/a.py").write_text("new\n")
    profile = profile_for("a.py", git_blob_sha(b"old\n"), "repl/a.py")
    with pytest.raises(RuntimeError, match="état amont inattendu"):
        apply_profile(target, profile, package)


def test_text_patch_and_rollback(tmp_path):
    package = tmp_path / "package"
    package.mkdir()
    target = tmp_path / "target"
    target.mkdir()
    old = b"x = image\n"
    (target / "resource.py").write_bytes(old)
    profile = profile_for(
        "resource.py",
        git_blob_sha(old),
        "",
        action="text_patch",
        patches=[{"old": "x = image", "new": "x = view"}],
    )
    apply_profile(target, profile, package)
    assert (target / "resource.py").read_text() == "x = view\n"
    rollback(target)
    assert (target / "resource.py").read_bytes() == old


def test_vendor_core_is_self_contained_and_rollback_removes_it(tmp_path):
    package = Path(__file__).parents[1]
    target = tmp_path / "target"
    target.mkdir()
    old = b"old\n"
    (target / "legacy.py").write_bytes(old)
    rel = "tests/_deployment_replacement.tmp"
    managed = package / rel
    managed.write_bytes(b"new\n")
    try:
        profile = profile_for("legacy.py", git_blob_sha(old), rel, vendor_core=True)
        apply_profile(target, profile, package)
        assert (target / "bnf_p0/__init__.py").exists()
        assert "httpx" in (target / "requirements-p0.txt").read_text()
        rollback(target)
        assert not (target / "bnf_p0").exists()
        assert not (target / "requirements-p0.txt").exists()
    finally:
        managed.unlink(missing_ok=True)
