#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if _SRC.exists() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from bnf_p0 import GallicaClient, __version__

try:
    from network_diagnose import diagnose
except ImportError:
    from scripts.network_diagnose import diagnose


def check(name, fn):
    started = time.time()
    try:
        value = fn()
        return {"name": name, "ok": True, "elapsed_s": round(time.time()-started, 3), "detail": value}
    except Exception as exc:
        return {"name": name, "ok": False, "elapsed_s": round(time.time()-started, 3), "error": f"{type(exc).__name__}: {exc}"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default="p0-live-report.json")
    args = ap.parse_args()
    network = diagnose()
    report = {"schema_version": 1, "package_version": __version__, "timestamp_utc": datetime.now(timezone.utc).isoformat(), "python": platform.python_version(), "network": network, "checks": []}
    if not network.get("ok"):
        report["ok"] = False
        report["status"] = "UNREACHABLE"
        report["reason"] = "gallica.bnf.fr n'est pas joignable depuis cet environnement; aucun verdict fonctionnel n'est possible."
    else:
        results = []
        with GallicaClient() as c:
            results.append(check("Pagination", lambda: {"views": c.view_count("bpt6k5738219s")}))
            results.append(check("OAIRecord", lambda: {"root_keys": sorted(c.oai_record("bpt6k5738219s").keys())[:10]}))
            results.append(check("Issues", lambda: {"resolved": c.issue_for_date("cb32798952c", date(1937,3,25))}))
            results.append(check("SRU", lambda: {"root_keys": sorted(c.sru('gallica all \"Verdun\"', maximum_records=1).keys())[:10]}))
            results.append(check("ALTO", lambda: {"bytes": len(c.alto("bpt6k5619759j", 3))}))
            results.append(check("IIIF info", lambda: {"width": int(c.iiif_info("btv1b53066668g", view=1)["width"])}))
        report["checks"] = results
        report["ok"] = all(r["ok"] for r in results)
        report["status"] = "PASS" if report["ok"] else "FAIL"
    text = json.dumps(report, ensure_ascii=False, indent=2)
    Path(args.output).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if report["ok"] else (2 if report["status"] == "UNREACHABLE" else 1)


if __name__ == "__main__":
    sys.exit(main())
