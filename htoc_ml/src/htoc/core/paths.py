"""Canonical HTOC share paths.

Import from here when a module needs a data location:

    from htoc.core.paths import share_root, opdiv_obs_template, noi_forecast_save_dir

Override the share root with ``HTOC_SHARE_ROOT``, or pass ``share=`` into a helper.
"""
from __future__ import annotations

import os
from pathlib import Path

# --- share root ---------------------------------------------------------------

DEFAULT_SHARE_ROOT = r"\\cscso1fsappv01\data\HTOC"
SHARE_ROOT_ENV = "HTOC_SHARE_ROOT"

# --- relative locations under the share ---------------------------------------

OPDIV_OBSERVATIONS_DIR = Path(r"Data_Analytics\Data\OpDiv_Observations")
OPDIV_OBS_FILENAME_TEMPLATE = "htoc_opdiv_obs_d{date}.csv"

OBSERVED_INDICATORS_DIR = Path(r"Data_Analytics\Data\Observed_Indicators")
OBSERVED_INDICATORS_FILENAME = "htoc_observed_indicators.csv"

OBSERVED_TAGS_DIR = Path(r"Data_Analytics\Data\Observed_Tags")
OBSERVED_TAGS_FILENAME = "htoc_observed_indicator_tags.csv"

THREATCONNECT_SDK_DIR = Path(r"Data_Analytics\threatconnect")

NOI_FORECAST_SAVE_DIR = Path(r"JA\NextObserveV4Test")
PRISM_SAVE_DIR = Path(r"JA\PrismTest")
THREAT_ASSESSMENT_SCORES_DIR = Path(r"Data_Analytics\Data\Threat Assessment Scores")
THREAT_ASSESSMENT_SCORES_FILENAME = "Threat_Assessment_Scores.xlsx"
THREAT_SCORE_IW_SAVE_DIR = Path(r"JA\ThreatScoreIwTest")

# ThreatConnect API-pull project (utils/config.json). Shared on the data share.
DEFAULT_TC_PROJECT_ROOT = (
    r"\\cscso1fsappv01\data\HTOC\Data_Analytics\ThrearConnect-api-pull"
)


def share_root(share: str | Path | None = None) -> Path:
    """HTOC data share root. ``share`` wins, else ``HTOC_SHARE_ROOT``, else default."""
    if share is not None and str(share).strip():
        return Path(str(share).strip())
    env = os.environ.get(SHARE_ROOT_ENV, "").strip()
    return Path(env or DEFAULT_SHARE_ROOT)


def env_path(name: str, default: Path | str) -> Path:
    """``Path`` from env var ``name``, or ``default`` when unset/blank."""
    raw = os.environ.get(name, "").strip()
    return Path(raw) if raw else Path(default)


def under_share(*parts: str | Path, share: str | Path | None = None) -> Path:
    """Join path segments under the share root."""
    out = share_root(share)
    for part in parts:
        out = out / part
    return out


# --- named data locations (pass share= to pin a root; otherwise uses share_root()) ---


def opdiv_obs_template(share: str | Path | None = None) -> str:
    """Daily OpDiv observation CSV template (``{date}`` = YYYYMMDD)."""
    return str(under_share(OPDIV_OBSERVATIONS_DIR, OPDIV_OBS_FILENAME_TEMPLATE, share=share))


def observed_indicators_csv(share: str | Path | None = None) -> Path:
    """Observed-indicators feed used by PRISM daily intake."""
    return under_share(OBSERVED_INDICATORS_DIR, OBSERVED_INDICATORS_FILENAME, share=share)


def observed_tags_csv(share: str | Path | None = None) -> Path:
    """Observed-indicator tags feed used by PRISM."""
    return under_share(OBSERVED_TAGS_DIR, OBSERVED_TAGS_FILENAME, share=share)


def threatconnect_sdk_dir(share: str | Path | None = None) -> Path:
    """ThreatConnect SDK / analytics package on the share."""
    return under_share(THREATCONNECT_SDK_DIR, share=share)


def noi_forecast_save_dir(share: str | Path | None = None) -> Path:
    """Next Observed Indicator forecast output directory."""
    return under_share(NOI_FORECAST_SAVE_DIR, share=share)


def prism_save_dir(share: str | Path | None = None) -> Path:
    """PRISM / Threat Assessment workbook output directory."""
    return under_share(PRISM_SAVE_DIR, share=share)


def threat_assessment_scores_xlsx(share: str | Path | None = None) -> Path:
    """PRISM scores workbook consumed by ThreatScoreIW."""
    return under_share(THREAT_ASSESSMENT_SCORES_DIR, THREAT_ASSESSMENT_SCORES_FILENAME, share=share)


def threat_score_iw_save_dir(share: str | Path | None = None) -> Path:
    """ThreatScoreIW daily workbook output directory."""
    return under_share(THREAT_SCORE_IW_SAVE_DIR, share=share)


def tc_project_root(project: str | Path | None = None) -> Path:
    """ThreatConnect API-pull project root (config.json lives under utils/)."""
    if project is not None and str(project).strip():
        return Path(str(project).strip())
    return env_path("PRISM_TC_PROJECT", DEFAULT_TC_PROJECT_ROOT)


def tc_config_json(project: str | Path | None = None) -> Path:
    return tc_project_root(project) / "utils" / "config.json"
