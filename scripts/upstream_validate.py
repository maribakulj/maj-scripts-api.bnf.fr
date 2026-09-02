#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import httpx

from bnf_p0.deploy import load_manifest

MANIFEST = ROOT / "deployment" / "upstream_manifest.json"
DEFAULT_OUTPUT = ROOT / "validation" / "upstream-sha-report.json"


def main() -> int:
    manifest = load_manifest(MANIFEST)
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "bnf-api-upstream-validator/0.2.0"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    rows = []
    with httpx.Client(timeout=20, follow_redirects=True, headers=headers) as client:
        for profile_name, profile in manifest["profiles"].items():
            repo = profile["repository"]
            branch = profile.get("default_branch", "master")
            for item in profile["files"]:
                path = item["path"]
                action = item["action"]
                expected = item.get("expected_blob_sha")
                url = f"https://api.github.com/repos/{repo}/contents/{path}"
                try:
                    response = client.get(url, params={"ref": branch})
                    if action == "create":
                        if response.status_code == 404:
                            actual = None
                            status = "PASS_ABSENT"
                            error = None
                        else:
                            response.raise_for_status()
                            actual = response.json().get("sha")
                            status = "COLLISION"
                            error = "file expected to be absent upstream already exists"
                    else:
                        response.raise_for_status()
                        actual = response.json().get("sha")
                        status = "PASS" if actual == expected else "DRIFT"
                        error = None
                except Exception as exc:
                    actual = None
                    status = "ERROR"
                    error = f"{type(exc).__name__}: {exc}"
                rows.append({
                    "profile": profile_name,
                    "repository": repo,
                    "path": path,
                    "action": action,
                    "expected_blob_sha": expected,
                    "actual_blob_sha": actual,
                    "status": status,
                    "error": error,
                })
    accepted = {"PASS", "PASS_ABSENT"}
    overall = "PASS" if rows and all(r["status"] in accepted for r in rows) else "FAIL"
    report = {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "manifest_version": manifest["package_version"],
        "status": overall,
        "rows": rows,
    }
    DEFAULT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if overall == "PASS" else 4


if __name__ == "__main__":
    raise SystemExit(main())
