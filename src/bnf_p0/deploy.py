from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATE_FILE = ".bnf-p0-state.json"
BACKUP_ROOT = ".bnf-p0-backup"
REQUIREMENTS = "httpx>=0.27,<1\npypdf>=5,<7\n"


@dataclass(frozen=True)
class FileStatus:
    path: str
    status: str
    actual_blob_sha: str | None
    expected_blob_sha: str | None
    detail: str = ""


def git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def accepted_blob_shas(data: bytes) -> set[str]:
    """Accepte le checkout LF ou CRLF d'un même fichier texte."""
    shas = {git_blob_sha(data)}
    if b"\r\n" in data:
        normalized = data.replace(b"\r\n", b"\n")
        shas.add(git_blob_sha(normalized))
    return shas


def load_manifest(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _replacement_bytes(package_root: Path, item: dict[str, Any]) -> bytes:
    return (package_root / item["source"]).read_bytes()


def _is_already_applied(target: Path, item: dict[str, Any], package_root: Path) -> bool:
    if not target.exists():
        return False
    if item["action"] in {"replace", "create"}:
        return target.read_bytes() == _replacement_bytes(package_root, item)
    if item["action"] == "text_patch":
        text = target.read_text(encoding="utf-8")
        # A replacement may legitimately contain the original substring
        # (for example inserting a new source() line after library(rvest)).
        # Presence of every replacement is therefore the stable/idempotent
        # criterion; requiring every old fragment to disappear is incorrect.
        return all(p["new"] in text for p in item["patches"])
    raise ValueError(f"Action inconnue: {item['action']}")


def inspect_profile(target_root: str | Path, profile: dict[str, Any], package_root: str | Path) -> list[FileStatus]:
    root = Path(target_root)
    pkg = Path(package_root)
    result: list[FileStatus] = []
    for item in profile["files"]:
        target = root / item["path"]
        expected = item.get("expected_blob_sha")
        action = item["action"]
        if not target.exists():
            if action == "create":
                result.append(FileStatus(item["path"], "EXPECTED_ABSENT", None, expected, "fichier à créer"))
            else:
                result.append(FileStatus(item["path"], "MISSING", None, expected, "fichier amont absent"))
            continue
        if _is_already_applied(target, item, pkg):
            result.append(FileStatus(item["path"], "ALREADY_APPLIED", git_blob_sha(target.read_bytes()), expected))
            continue
        data = target.read_bytes()
        actual = git_blob_sha(data)
        if action == "create":
            status = "DRIFT"
            detail = "un fichier non géré existe déjà à l'emplacement à créer"
        elif expected and expected in accepted_blob_shas(data):
            status = "EXPECTED"
            detail = "SHA amont conforme"
        else:
            status = "DRIFT"
            detail = "le fichier diffère de la version auditée"
        result.append(FileStatus(item["path"], status, actual, expected, detail))
    return result


def _backup_path(backup_dir: Path, relative: str) -> Path:
    return backup_dir / relative


def _backup_existing(root: Path, rel: str, backup_dir: Path) -> bool:
    src = root / rel
    if not src.exists():
        return False
    dst = _backup_path(backup_dir, rel)
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        shutil.copytree(src, dst)
    else:
        shutil.copy2(src, dst)
    return True


def _write_managed_file(root: Path, rel: str, data: bytes, backup_dir: Path, state: dict[str, Any]) -> None:
    target = root / rel
    existed = _backup_existing(root, rel, backup_dir)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    state["changes"].append({"path": rel, "kind": "file", "existed": existed})


def _vendor_core(root: Path, package_root: Path, backup_dir: Path, state: dict[str, Any], force: bool) -> None:
    src = package_root / "src" / "bnf_p0"
    dst = root / "bnf_p0"
    if dst.exists():
        same = all(
            (dst / p.relative_to(src)).exists() and (dst / p.relative_to(src)).read_bytes() == p.read_bytes()
            for p in src.rglob("*") if p.is_file()
        )
        if same:
            state["notes"].append("bnf_p0 déjà vendorisé à l'identique")
        else:
            if not force:
                raise RuntimeError("Un dossier bnf_p0 existe déjà et diffère. Utiliser --force pour le sauvegarder/remplacer.")
            _backup_existing(root, "bnf_p0", backup_dir)
            shutil.rmtree(dst)
            shutil.copytree(src, dst)
            state["changes"].append({"path": "bnf_p0", "kind": "dir", "existed": True})
    else:
        shutil.copytree(src, dst)
        state["changes"].append({"path": "bnf_p0", "kind": "dir", "existed": False})

    req = root / "requirements-p0.txt"
    if not req.exists() or req.read_text(encoding="utf-8") != REQUIREMENTS:
        _write_managed_file(root, "requirements-p0.txt", REQUIREMENTS.encode("utf-8"), backup_dir, state)


def apply_profile(target_root: str | Path, profile: dict[str, Any], package_root: str | Path, *, force: bool = False) -> dict[str, Any]:
    root = Path(target_root).resolve()
    pkg = Path(package_root).resolve()
    statuses = inspect_profile(root, profile, pkg)
    blockers = [s for s in statuses if s.status in {"MISSING", "DRIFT"}]
    if blockers and not force:
        detail = ", ".join(f"{b.path}:{b.status}" for b in blockers)
        raise RuntimeError(f"Déploiement refusé: état amont inattendu ({detail}). Relancer avec --force seulement après revue.")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_dir = root / BACKUP_ROOT / timestamp
    backup_dir.mkdir(parents=True, exist_ok=False)
    state: dict[str, Any] = {
        "schema_version": 1,
        "applied_at_utc": timestamp,
        "repository": profile.get("repository"),
        "backup_dir": str(backup_dir.relative_to(root)),
        "changes": [],
        "notes": [],
    }

    if profile.get("vendor_core"):
        _vendor_core(root, pkg, backup_dir, state, force)

    for item in profile["files"]:
        target = root / item["path"]
        if _is_already_applied(target, item, pkg):
            state["notes"].append(f"déjà appliqué: {item['path']}")
            continue
        existed = _backup_existing(root, item["path"], backup_dir)
        target.parent.mkdir(parents=True, exist_ok=True)
        if item["action"] in {"replace", "create"}:
            target.write_bytes(_replacement_bytes(pkg, item))
        elif item["action"] == "text_patch":
            text = target.read_text(encoding="utf-8")
            for patch in item["patches"]:
                old, new = patch["old"], patch["new"]
                if new in text:
                    continue
                if old not in text:
                    raise RuntimeError(f"Motif de patch introuvable dans {item['path']}: {old}")
                text = text.replace(old, new, 1)
            target.write_text(text, encoding="utf-8")
        else:
            raise ValueError(f"Action inconnue: {item['action']}")
        state["changes"].append({"path": item["path"], "kind": "file", "existed": existed})

    (root / STATE_FILE).write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return state


def verify_profile(target_root: str | Path, profile: dict[str, Any], package_root: str | Path) -> tuple[bool, list[FileStatus], list[str]]:
    root = Path(target_root)
    statuses = inspect_profile(root, profile, package_root)
    problems: list[str] = []
    for status in statuses:
        if status.status != "ALREADY_APPLIED":
            problems.append(f"{status.path}: {status.status}")
    if profile.get("vendor_core"):
        if not (root / "bnf_p0" / "__init__.py").exists():
            problems.append("bnf_p0 vendorisé absent")
        if not (root / "requirements-p0.txt").exists():
            problems.append("requirements-p0.txt absent")
    return not problems, statuses, problems


def rollback(target_root: str | Path) -> dict[str, Any]:
    root = Path(target_root).resolve()
    state_path = root / STATE_FILE
    if not state_path.exists():
        raise RuntimeError(f"{STATE_FILE} absent: aucun déploiement géré à annuler")
    state = json.loads(state_path.read_text(encoding="utf-8"))
    backup_dir = root / state["backup_dir"]

    for change in reversed(state["changes"]):
        rel = change["path"]
        target = root / rel
        backup = backup_dir / rel
        if change["existed"]:
            if target.is_dir():
                shutil.rmtree(target)
            elif target.exists():
                target.unlink()
            target.parent.mkdir(parents=True, exist_ok=True)
            if backup.is_dir():
                shutil.copytree(backup, target)
            else:
                shutil.copy2(backup, target)
        else:
            if target.is_dir():
                shutil.rmtree(target)
            elif target.exists():
                target.unlink()

    state_path.unlink()
    return state
