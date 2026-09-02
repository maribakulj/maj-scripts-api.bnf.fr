#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "validation" / "public-documentation-report.json"

PAGES = {
    "wrappers": "https://api.bnf.fr/fr/wrapper-python-pour-les-api-gallica",
    "pyllica": "https://api.bnf.fr/fr/extracteur-python-de-corpus-de-periodiques",
    "iiif": "https://api.bnf.fr/fr/api-iiif-de-recuperation-des-images-de-gallica",
    "quotas": "https://api.bnf.fr/fr/node/232",
}


def plain(html: str) -> str:
    text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def check_contains(text: str, *parts: str) -> tuple[bool, str]:
    missing = [part for part in parts if part.casefold() not in text.casefold()]
    return not missing, "" if not missing else "missing: " + ", ".join(missing)


def main() -> int:
    headers = {
        "User-Agent": "maj-scripts-api-bnf-doc-validator/0.2.0 (+https://github.com/maribakulj/maj-scripts-api.bnf.fr)"
    }
    rows: list[dict[str, object]] = []

    with httpx.Client(timeout=30, follow_redirects=True, headers=headers) as client:
        bodies: dict[str, str] = {}
        for name, url in PAGES.items():
            try:
                response = client.get(url)
                response.raise_for_status()
                bodies[name] = plain(response.text)
                rows.append({"check": f"fetch:{name}", "status": "PASS", "http": response.status_code, "url": url})
            except Exception as exc:
                rows.append({"check": f"fetch:{name}", "status": "FAIL", "url": url, "error": f"{type(exc).__name__}: {exc}"})

        if "quotas" in bodies:
            ok, detail = check_contains(
                bodies["quotas"],
                "5 appels",
                "4 appels",
                "50 appels",
                "429",
                "Too Many Requests",
            )
            rows.append({"check": "quota-contract", "status": "PASS" if ok else "DRIFT", "detail": detail})

        if "iiif" in bodies:
            text = bodies["iiif"]
            # The public technical sheet currently says Version 2. Keep this
            # deliberately strict: if the public contract changes, editorial
            # copy must be reviewed rather than silently lying.
            version_2 = bool(re.search(r"Version\s+2(?:\s|$)", text, flags=re.I))
            rows.append({
                "check": "iiif-public-version-2",
                "status": "PASS" if version_2 else "DRIFT",
                "detail": "public technical sheet no longer clearly exposes Version 2" if not version_2 else "",
            })

        if "wrappers" in bodies:
            ok, detail = check_contains(bodies["wrappers"], "PyGallica", "Gallipy", "fdh-gallica", "Pyllica", "bnfimage", "gargallica")
            rows.append({"check": "wrapper-list-contract", "status": "PASS" if ok else "DRIFT", "detail": detail})

        if "pyllica" in bodies:
            ok, detail = check_contains(bodies["pyllica"], "full/3000", "full/5000")
            rows.append({
                "check": "pyllica-hd-examples-still-present",
                "status": "PASS" if ok else "CHANGED",
                "detail": detail,
                "note": "This is an observation, not a normative requirement; removal after CMS update is expected.",
            })

    hard_fail = any(row["status"] in {"FAIL", "DRIFT"} for row in rows)
    report = {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "FAIL" if hard_fail else "PASS",
        "rows": rows,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 4 if hard_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
