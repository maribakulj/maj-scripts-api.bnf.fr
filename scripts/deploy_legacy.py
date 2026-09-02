#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from bnf_p0.deploy import apply_profile, inspect_profile, load_manifest, rollback, verify_profile

MANIFEST = ROOT / "deployment" / "upstream_manifest.json"


def main() -> int:
    manifest = load_manifest(MANIFEST)
    parser = argparse.ArgumentParser(description="Déploiement P0 sûr dans un checkout d'un wrapper historique Gallica.")
    parser.add_argument("command", choices=["plan", "apply", "verify", "rollback"])
    parser.add_argument("--profile", choices=sorted(manifest["profiles"]), required=False)
    parser.add_argument("--target", required=True, help="Racine du checkout du dépôt à corriger")
    parser.add_argument("--force", action="store_true", help="Autorise un fichier amont ayant dérivé, après sauvegarde")
    args = parser.parse_args()

    if args.command != "rollback" and not args.profile:
        parser.error("--profile est requis sauf pour rollback")

    target = Path(args.target)
    if args.command == "rollback":
        state = rollback(target)
        print(json.dumps({"status": "ROLLED_BACK", "repository": state.get("repository")}, ensure_ascii=False, indent=2))
        return 0

    profile = manifest["profiles"][args.profile]
    if args.command == "plan":
        rows = inspect_profile(target, profile, ROOT)
        for row in rows:
            print(f"{row.status:16} {row.path} {row.detail}")
        bad = any(r.status in {"MISSING", "DRIFT"} for r in rows)
        return 2 if bad else 0

    if args.command == "apply":
        state = apply_profile(target, profile, ROOT, force=args.force)
        print(json.dumps({"status": "APPLIED", "repository": state.get("repository"), "backup_dir": state["backup_dir"]}, ensure_ascii=False, indent=2))
        return 0

    ok, rows, problems = verify_profile(target, profile, ROOT)
    for row in rows:
        print(f"{row.status:16} {row.path}")
    if problems:
        print("PROBLEMS:")
        for p in problems:
            print(f"- {p}")
    return 0 if ok else 3


if __name__ == "__main__":
    raise SystemExit(main())
