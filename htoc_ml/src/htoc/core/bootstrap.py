"""Ensure ``import htoc`` works from notebooks and ad-hoc scripts.

Prefer an editable install (``uv pip install -e ./htoc_ml``) or setting
``PYTHONPATH`` to ``htoc_ml/src``. When neither is configured, call
:func:`ensure_htoc_on_path` before other ``htoc`` imports.
"""
from __future__ import annotations

import os
import sys
from collections.abc import Sequence
from pathlib import Path

_INSTALL_HINT = (
    "htoc not found. Add htoc_ml/src to PYTHONPATH or run "
    "`uv pip install -e ./htoc_ml` from the repo root with this kernel."
)


def htoc_src_dir() -> Path:
    """Return ``htoc_ml/src`` (the directory that contains the ``htoc`` package)."""
    return Path(__file__).resolve().parents[2]


def _search_bases(
    start: Path | str | None,
    extra_roots: Sequence[Path | str],
) -> list[Path]:
    bases: list[Path] = []
    seen: set[Path] = set()

    def add(base: Path) -> None:
        resolved = base.resolve()
        if resolved not in seen:
            seen.add(resolved)
            bases.append(resolved)

    if start is not None:
        add(Path(start))
    else:
        add(Path.cwd())

    for base in list(bases):
        add(base)
        for parent in base.parents:
            add(parent)

    for root in extra_roots:
        add(Path(root))

    for parent in htoc_src_dir().parents:
        add(parent)

    return bases


def find_htoc_src(
    *,
    start: Path | str | None = None,
    extra_roots: Sequence[Path | str] | None = None,
) -> Path | None:
    """Locate ``htoc_ml/src`` by walking upward from ``start`` (default: cwd)."""
    roots = list(extra_roots or ())
    repo_root = os.environ.get("HTOC_REPO_ROOT", "").strip()
    if repo_root:
        roots.append(repo_root)

    for base in _search_bases(start, roots):
        src = base / "htoc_ml" / "src"
        if (src / "htoc").is_dir():
            return src
    return None


def ensure_htoc_on_path(
    *,
    start: Path | str | None = None,
    extra_roots: Sequence[Path | str] | None = None,
) -> Path:
    """Add ``htoc_ml/src`` to ``sys.path`` when needed so ``import htoc`` works.

    Idempotent. Returns the ``src`` directory (already importable or newly added).
    """
    try:
        import htoc
    except ModuleNotFoundError:
        src = find_htoc_src(start=start, extra_roots=extra_roots)
        if src is None:
            raise ModuleNotFoundError(_INSTALL_HINT) from None
        src_s = str(src)
        if src_s not in sys.path:
            sys.path.insert(0, src_s)
        return src

    return Path(htoc.__file__).resolve().parent.parent
