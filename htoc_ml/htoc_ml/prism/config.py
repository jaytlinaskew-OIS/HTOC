"""PRISM / Threat Assessment paths and intake presets."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from htoc_ml.core.pipeline import PipelineError

DEFAULT_SHARE = r"\\cscso1fsappv01\data\HTOC"
DEFAULT_TC_PROJECT = r"\\cscso1fsappv01\home\jaskew\HTOC\scripts\Data Movement\ThrearConnect-api-pull"

WEEKLY_TYPES = (
    "Address", "EmailAddress", "File", "Host", "URL", "ASN", "CIDR",
    "Email Subject", "Hashtag", "Mutex", "Registry Key", "User Agent", "Stripped URL",
)
DAILY_TYPES = (
    "Address", "EmailAddress", "File", "Host", "URL", "ASN", "CIDR",
    "Email Subject", "Hashtag", "Mutex", "Registry Key", "User Agent",
)
WEEKLY_OWNERS = (
    "HTOC Org",
    "CISA Federal Feed",
    "CMS_CTI",
    "Crowdstrike Falcon Intelligence",
    "DHS CISCP",
    "Intel471",
    "Mandiant Advantage Threat Intelligence",
    "VA_TIP Data",
)
DAILY_OWNERS = (
    "HTOC Org",
    "CISA Federal Feed",
    "CMS_CTI",
    "Crowdstrike Falcon Intelligence",
    "DHS CISCP",
    "Intel 471 Intelligence",
    "Mandiant Advantage Threat Intelligence",
    "VA_TIP Data",
    "Google Threat Intelligence",
)
WEEKLY_STANDALONE_EXTRA = frozenset({"tor node"})


@dataclass(frozen=True)
class PrismConfig:
    mode: str = "daily"
    htoc_share_root: str = DEFAULT_SHARE
    tc_project_root: str = DEFAULT_TC_PROJECT
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
        object.__setattr__(self, "htoc_share_root", self.htoc_share_root.strip() or DEFAULT_SHARE)
        share = Path(self.htoc_share_root)
        if not self.config_path:
            object.__setattr__(self, "config_path", str(Path(self.tc_project_root) / "utils" / "config.json"))
        if not self.tc_sdk_path:
            object.__setattr__(self, "tc_sdk_path", str(share / "Data_Analytics" / "threatconnect"))
        if not self.observed_indicators_csv:
            object.__setattr__(
                self,
                "observed_indicators_csv",
                str(share / r"Data_Analytics\Data\Observed_Indicators\htoc_observed_indicators.csv"),
            )
        if not self.tags_csv:
            object.__setattr__(
                self,
                "tags_csv",
                str(share / r"Data_Analytics\Data\Observed_Tags\htoc_observed_indicator_tags.csv"),
            )
        if not self.opdiv_template:
            object.__setattr__(
                self,
                "opdiv_template",
                str(share / r"Data_Analytics\Data\OpDiv_Observations\htoc_opdiv_obs_d{date}.csv"),
            )
        if not self.save_dir:
            object.__setattr__(self, "save_dir", str(share / r"JA\PrismTest"))

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
        mode = os.environ.get("PRISM_MODE", "daily").strip().lower() or "daily"
        share = os.environ.get("HTOC_SHARE_ROOT", DEFAULT_SHARE)
        kwargs = {
            "htoc_share_root": share,
            "tc_project_root": os.environ.get("PRISM_TC_PROJECT", DEFAULT_TC_PROJECT),
            "config_path": os.environ.get("PRISM_CONFIG_PATH", ""),
            "save_dir": os.environ.get("PRISM_SAVE_DIR", ""),
        }
        if mode == "weekly":
            return cls.weekly(**kwargs)
        return cls.daily(**kwargs)
