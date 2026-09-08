#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
for _candidate in (_ROOT, _ROOT / "src"):
    if (_candidate / "bnf_p0" / "__init__.py").exists() and str(_candidate) not in sys.path:
        sys.path.insert(0, str(_candidate))

from bnf_p0.pdf_tools import download_pdf


def main():
    p = argparse.ArgumentParser(description="Télécharge un PDF Gallica par blocs, avec quotas et pypdf moderne.")
    p.add_argument("ark")
    p.add_argument("outputfile")
    p.add_argument("-s", "--start", type=int, default=1)
    p.add_argument("-e", "--end", type=int)
    p.add_argument("--blocksize", type=int, default=100)
    p.add_argument("--source", choices=["iiif", "web"], default="iiif",
                   help="iiif: reconstruit depuis les images (défaut) ; "
                        "web: route .pdf historique, aujourd'hui protégée")
    p.add_argument("--width", type=int, default=1000,
                   help="largeur des images IIIF ; au-delà de 1000 px, "
                        "la classe limitée à 5 appels/minute s'applique")
    args = p.parse_args()
    path = download_pdf(args.ark, args.outputfile, start=args.start, end=args.end,
                        block_size=args.blocksize, source=args.source, width=args.width)
    print(path)


if __name__ == "__main__":
    main()
