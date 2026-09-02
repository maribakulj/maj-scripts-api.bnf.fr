#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import socket
import ssl
from datetime import datetime, timezone
from pathlib import Path

HOST = "gallica.bnf.fr"
PORT = 443


def diagnose() -> dict:
    report = {"timestamp_utc": datetime.now(timezone.utc).isoformat(), "host": HOST, "dns": {"ok": False}, "tls": {"ok": False}}
    try:
        infos = socket.getaddrinfo(HOST, PORT, type=socket.SOCK_STREAM)
        addresses = sorted({item[4][0] for item in infos})
        report["dns"] = {"ok": True, "addresses": addresses}
    except Exception as exc:
        report["dns"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
        report["ok"] = False
        return report
    try:
        context = ssl.create_default_context()
        with socket.create_connection((HOST, PORT), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=HOST) as tls:
                cert = tls.getpeercert()
                report["tls"] = {"ok": True, "protocol": tls.version(), "cipher": tls.cipher()[0] if tls.cipher() else None, "not_after": cert.get("notAfter")}
    except Exception as exc:
        report["tls"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    report["ok"] = bool(report["dns"]["ok"] and report["tls"]["ok"])
    return report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output")
    args = ap.parse_args()
    report = diagnose()
    text = json.dumps(report, ensure_ascii=False, indent=2)
    print(text)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
