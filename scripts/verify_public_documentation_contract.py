#!/usr/bin/env python3
"""Surveillance de la dérive de la documentation publique d'api.bnf.fr.

Ce script distingue deux situations que l'on confondait auparavant :

- le site a changé — c'est une dérive documentaire, un signal éditorial ;
- le site n'a pas répondu — c'est un incident réseau, pas une dérive.

Sans cette distinction, une lenteur d'api.bnf.fr se présente comme une dérive.
Le workflow tournant chaque lundi, le vrai signal finirait noyé dans le bruit.
C'est le même partage que `live_validate.py` applique déjà à Gallica.
"""

from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "validation" / "public-documentation-report.json"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from network_diagnose import diagnose  # noqa: E402

HOST = "api.bnf.fr"

PAGES = {
    "wrappers": "https://api.bnf.fr/fr/wrapper-python-pour-les-api-gallica",
    "pyllica": "https://api.bnf.fr/fr/extracteur-python-de-corpus-de-periodiques",
    "iiif": "https://api.bnf.fr/fr/api-iiif-de-recuperation-des-images-de-gallica",
    "quotas": "https://api.bnf.fr/fr/node/232",
}

TIMEOUT = 60.0
ATTEMPTS = 3
BACKOFF = 4.0

# Codes de sortie, alignés sur live_validate.py
EXIT_PASS = 0
EXIT_UNREACHABLE = 2
EXIT_DRIFT = 4


def plain(html: str) -> str:
    text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def check_contains(text: str, *parts: str) -> tuple[bool, str]:
    missing = [part for part in parts if part.casefold() not in text.casefold()]
    return not missing, "" if not missing else "missing: " + ", ".join(missing)


def overall_status(rows: list[dict]) -> str:
    """Verdict global.

    Une dérive l'emporte sur une indisponibilité : si une page a pu être lue et
    qu'elle a changé, c'est un signal éditorial même si une autre page est
    injoignable. À l'inverse, une page injoignable n'est jamais une dérive.
    """
    statuses = {str(row.get("status")) for row in rows}
    if "DRIFT" in statuses or "FAIL" in statuses:
        return "FAIL"
    if "UNREACHABLE" in statuses:
        return "UNREACHABLE"
    return "PASS"


def fetch(client: httpx.Client, url: str) -> tuple[str | None, str | None, int | None]:
    """Récupère une page, avec plusieurs tentatives espacées."""
    last_error: str | None = None
    for attempt in range(1, ATTEMPTS + 1):
        try:
            response = client.get(url)
            response.raise_for_status()
            return plain(response.text), None, response.status_code
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            if attempt < ATTEMPTS:
                time.sleep(BACKOFF * attempt)
    return None, last_error, None


def main() -> int:
    headers = {
        "User-Agent": "maj-scripts-api-bnf-doc-validator/0.2.0 (+https://github.com/maribakulj/maj-scripts-api.bnf.fr)"
    }
    rows: list[dict[str, object]] = []
    network = diagnose(HOST)

    with httpx.Client(timeout=TIMEOUT, follow_redirects=True, headers=headers) as client:
        bodies: dict[str, str] = {}
        for name, url in PAGES.items():
            body, error, code = fetch(client, url)
            if body is None:
                rows.append({
                    "check": f"fetch:{name}",
                    "status": "UNREACHABLE",
                    "url": url,
                    "error": error,
                    "attempts": ATTEMPTS,
                    "note": "Page injoignable depuis cet environnement : aucune conclusion documentaire n'est possible pour cette page.",
                })
                continue
            bodies[name] = body
            rows.append({"check": f"fetch:{name}", "status": "PASS", "http": code, "url": url})

        def skipped(check: str, page: str) -> None:
            rows.append({
                "check": check,
                "status": "SKIPPED",
                "detail": f"page '{page}' injoignable",
            })

        if "quotas" in bodies:
            ok, detail = check_contains(
                bodies["quotas"], "5 appels", "4 appels", "50 appels", "429", "Too Many Requests",
            )
            rows.append({"check": "quota-contract", "status": "PASS" if ok else "DRIFT", "detail": detail})
        else:
            skipped("quota-contract", "quotas")

        if "iiif" in bodies:
            # La fiche technique publique indique actuellement Version 2. Ce
            # contrôle reste volontairement strict : si le contrat public
            # change, la copie éditoriale doit être revue plutôt que de mentir.
            version_2 = bool(re.search(r"Version\s+2(?:\s|$)", bodies["iiif"], flags=re.I))
            rows.append({
                "check": "iiif-public-version-2",
                "status": "PASS" if version_2 else "DRIFT",
                "detail": "" if version_2 else "public technical sheet no longer clearly exposes Version 2",
            })
        else:
            skipped("iiif-public-version-2", "iiif")

        if "wrappers" in bodies:
            ok, detail = check_contains(
                bodies["wrappers"], "PyGallica", "Gallipy", "fdh-gallica", "Pyllica", "bnfimage", "gargallica",
            )
            rows.append({"check": "wrapper-list-contract", "status": "PASS" if ok else "DRIFT", "detail": detail})
        else:
            skipped("wrapper-list-contract", "wrappers")

        if "pyllica" in bodies:
            ok, detail = check_contains(bodies["pyllica"], "full/3000", "full/5000")
            rows.append({
                "check": "pyllica-hd-examples-still-present",
                "status": "PASS" if ok else "CHANGED",
                "detail": detail,
                "note": "This is an observation, not a normative requirement; removal after CMS update is expected.",
            })
        else:
            skipped("pyllica-hd-examples-still-present", "pyllica")

    status = overall_status(rows)
    report = {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "network": network,
        "rows": rows,
    }
    if status == "UNREACHABLE":
        report["reason"] = (
            f"{HOST} n'a pas répondu depuis cet environnement après "
            f"{ATTEMPTS} tentatives ; aucune dérive documentaire n'est constatée."
        )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return {"PASS": EXIT_PASS, "UNREACHABLE": EXIT_UNREACHABLE, "FAIL": EXIT_DRIFT}[status]


if __name__ == "__main__":
    raise SystemExit(main())
