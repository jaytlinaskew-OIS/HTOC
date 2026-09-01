"""Share-root helpers for analyst tools. Re-exports the canonical paths module."""
from __future__ import annotations

from htoc_ml.core.paths import DEFAULT_SHARE_ROOT, env_path, share_root

# Back-compat alias used by older tool imports
DEFAULT_SHARE = DEFAULT_SHARE_ROOT

__all__ = ["DEFAULT_SHARE", "DEFAULT_SHARE_ROOT", "env_path", "share_root"]
