"""PRISM / Threat Assessment paths and intake presets."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from htoc_ml.core import paths as htoc_paths
from htoc_ml.core.pipeline import PipelineError
from htoc_ml.core.threatconnect_presets import (
    INDICATOR_TYPES_DAILY,
    INDICATOR_TYPES_WEEKLY,
    OWNERS_DAILY,
    OWNERS_WEEKLY,
)

WEEKLY_TYPES = INDICATOR_TYPES_WEEKLY
DAILY_TYPES = INDICATOR_TYPES_DAILY
WEEKLY_OWNERS = OWNERS_WEEKLY
DAILY_OWNERS = OWNERS_DAILY
WEEKLY_STANDALONE_EXTRA = frozenset({"tor node"})


@dataclass(frozen=True)
class PrismConfig:
    mode: str = "daily"
    htoc_share_root: str = htoc_paths.DEFAULT_SHARE_ROOT
    tc_project_root: str = htoc_paths.DEFAULT_TC_PROJECT_ROOT
    config_path: str = ""
    tc_sdk_path: str = ""
    observed_indicators_csv: str = ""
    tags_csv: str = ""
    opdiv_template: str = ""
    save_dir: str = ""
    excel_filename: str = "Threat_Assessment_Scores.xlsx"
    query_lookback_days: int = 7
    firstseen_lookback_days: int = 7
    opdiv_lookback_days: int = 365
    result_page_size: int = 500
    indicator_types: tuple[str, ...] = DAILY_TYPES
    owner_names: tuple[str, ...] = DAILY_OWNERS
    extra_standalone_tags: frozenset[str] = field(default_factory=frozenset)
    threat_category: str = "THREAT ACTOR"

    def __post_init__(self) -> None:
        if self.mode not in {"daily", "weekly"}:
            raise PipelineError(f"mode must be 'daily' or 'weekly', got {self.mode!r}")
        share = self.htoc_share_root.strip() or htoc_paths.DEFAULT_SHARE_ROOT
        object.__setattr__(self, "htoc_share_root", share)
        tc_root = self.tc_project_root.strip() or htoc_paths.DEFAULT_TC_PROJECT_ROOT
        object.__setattr__(self, "tc_project_root", tc_root)
        if not self.config_path:
            object.__setattr__(self, "config_path", str(htoc_paths.tc_config_json(tc_root)))
        if not self.tc_sdk_path:
            object.__setattr__(self, "tc_sdk_path", str(htoc_paths.threatconnect_sdk_dir(share)))
        if not self.observed_indicators_csv:
            object.__setattr__(
                self, "observed_indicators_csv", str(htoc_paths.observed_indicators_csv(share))
            )
        if not self.tags_csv:
            object.__setattr__(self, "tags_csv", str(htoc_paths.observed_tags_csv(share)))
        if not self.opdiv_template:
            object.__setattr__(self, "opdiv_template", htoc_paths.opdiv_obs_template(share))
        if not self.save_dir:
            object.__setattr__(self, "save_dir", str(htoc_paths.prism_save_dir(share)))

    @property
    def excel_path(self) -> Path:
        return Path(self.save_dir) / self.excel_filename

    @classmethod
    def daily(cls, **kwargs) -> "PrismConfig":
        return cls(mode="daily", opdiv_lookback_days=365, **kwargs)

    @classmethod
    def weekly(cls, **kwargs) -> "PrismConfig":
        return cls(
            mode="weekly",
            indicator_types=WEEKLY_TYPES,
            owner_names=WEEKLY_OWNERS,
            extra_standalone_tags=WEEKLY_STANDALONE_EXTRA,
            **kwargs,
        )

    @classmethod
    def from_env(cls) -> "PrismConfig":
        try:
            mode = os.environ.get("PRISM_MODE", "daily").strip().lower() or "daily"
            kwargs = {
                "htoc_share_root": str(htoc_paths.share_root()),
                "tc_project_root": str(htoc_paths.tc_project_root()),
                "config_path": os.environ.get("PRISM_CONFIG_PATH", ""),
                "save_dir": os.environ.get("PRISM_SAVE_DIR", ""),
            }
            if mode == "weekly":
                return cls.weekly(**kwargs)
            if mode != "daily":
                raise PipelineError(f"PRISM_MODE must be 'daily' or 'weekly', got {mode!r}")
            return cls.daily(**kwargs)
        except PipelineError:
            raise
        except (ValueError, TypeError) as exc:
            raise PipelineError(f"invalid PRISM env config: {exc}") from exc
