"""Remplacement drop-in P0 de PyGallica/python3/iiif_api.py."""
from pathlib import Path as _Path
import sys as _sys
try:
    import bnf_p0 as _bnf_p0_check
except ModuleNotFoundError:
    for _parent in _Path(__file__).resolve().parents:
        if (_parent / "bnf_p0" / "__init__.py").exists():
            _sys.path.insert(0, str(_parent))
            break
from bnf_p0.compat.pygallica import IIIF
__all__ = ["IIIF"]
