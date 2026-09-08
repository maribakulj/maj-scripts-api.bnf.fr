from pathlib import Path

import pytest

from bnf_p0.deploy import apply_profile, git_blob_sha, rollback, verify_profile


def profile_for(path: str, expected: str | None, source: str, *, vendor_core=False, action="replace", patches=None):
    item = {"path": path, "action": action}
    if expected is not None:
        item["expected_blob_sha"] = expected
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


def test_create_verify_and_rollback_removes_created_file(tmp_path):
    package = tmp_path / "package"
    target = tmp_path / "target"
    (package / "repl").mkdir(parents=True)
    target.mkdir()
    (package / "repl/helper.R").write_text("helper <- TRUE\n")
    profile = profile_for("helper.R", None, "repl/helper.R", action="create")

    apply_profile(target, profile, package)
    assert (target / "helper.R").read_text() == "helper <- TRUE\n"
    ok, _, problems = verify_profile(target, profile, package)
    assert ok and not problems

    rollback(target)
    assert not (target / "helper.R").exists()


def test_create_refuses_collision_without_force(tmp_path):
    package = tmp_path / "package"
    target = tmp_path / "target"
    (package / "repl").mkdir(parents=True)
    target.mkdir()
    (package / "repl/helper.R").write_text("managed <- TRUE\n")
    (target / "helper.R").write_text("user <- TRUE\n")
    profile = profile_for("helper.R", None, "repl/helper.R", action="create")

    with pytest.raises(RuntimeError, match="état amont inattendu"):
        apply_profile(target, profile, package)


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


def _vendor_profile():
    return {
        "repository": "exemple/tiers",
        "vendor_core": True,
        "files": [],
    }


def test_recompiling_the_core_does_not_block_a_second_apply(tmp_path):
    """Un simple import régénère un .pyc dans la source. Si le déployeur le
    vendorise et le compare, le redéploiement suivant se croit face à une
    dérive et exige --force pour un non-événement."""
    from bnf_p0.deploy import apply_profile

    package_root = tmp_path / "paquet"
    core = package_root / "src" / "bnf_p0"
    core.mkdir(parents=True)
    (core / "__init__.py").write_text("# coeur\n", encoding="utf-8")

    target = tmp_path / "tiers"
    target.mkdir()

    apply_profile(target, _vendor_profile(), package_root)

    # Python compile le cœur au premier import : un cache apparaît côté source.
    cache = core / "__pycache__"
    cache.mkdir()
    (cache / "__init__.cpython-312.pyc").write_bytes(b"\x00cache\x00")

    # Le second déploiement doit passer sans --force.
    apply_profile(target, _vendor_profile(), package_root)


def test_compiled_caches_are_never_copied_into_a_third_party_checkout(tmp_path):
    from bnf_p0.deploy import apply_profile

    package_root = tmp_path / "paquet"
    core = package_root / "src" / "bnf_p0"
    (core / "__pycache__").mkdir(parents=True)
    (core / "__init__.py").write_text("# coeur\n", encoding="utf-8")
    (core / "__pycache__" / "__init__.cpython-312.pyc").write_bytes(b"\x00cache\x00")

    target = tmp_path / "tiers"
    target.mkdir()
    apply_profile(target, _vendor_profile(), package_root)

    assert (target / "bnf_p0" / "__init__.py").exists()
    assert not (target / "bnf_p0" / "__pycache__").exists()
    assert not list((target / "bnf_p0").rglob("*.pyc"))


def test_two_deployments_in_the_same_second_keep_both_backups(tmp_path):
    """L'horodatage des sauvegardes est à la seconde ; deux déploiements
    rapprochés ne doivent ni planter ni écraser la sauvegarde précédente."""
    from bnf_p0.deploy import apply_profile

    package_root = tmp_path / "paquet"
    core = package_root / "src" / "bnf_p0"
    core.mkdir(parents=True)
    (core / "__init__.py").write_text("# coeur\n", encoding="utf-8")

    target = tmp_path / "tiers"
    target.mkdir()

    first = apply_profile(target, _vendor_profile(), package_root)
    second = apply_profile(target, _vendor_profile(), package_root)

    assert first["backup_dir"] != second["backup_dir"]
    assert (target / first["backup_dir"]).exists()
    assert (target / second["backup_dir"]).exists()
