"""Compatibility wrapper package for clean_interfaces."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_SRC_PACKAGE = Path(__file__).resolve().parent.parent / "src" / "clean_interfaces"
_SRC_ROOT = _SRC_PACKAGE.parent
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))
_SPEC = importlib.util.spec_from_file_location(__name__, _SRC_PACKAGE / "__init__.py")
if _SPEC is None or _SPEC.loader is None:
    error_message = "Unable to load clean_interfaces package from src directory"
    raise ImportError(error_message)
_MODULE = importlib.util.module_from_spec(_SPEC)
sys.modules[__name__] = _MODULE
_SPEC.loader.exec_module(_MODULE)
globals().update(_MODULE.__dict__)
