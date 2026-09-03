"""ThreatConnect helpers for PRISM (re-exports shared core client)."""
from __future__ import annotations

from htoc.core.threatconnect import ThreatConnectClient, load_api_config
from htoc.prism.config import PrismConfig


def connect_threatconnect(config: PrismConfig) -> ThreatConnectClient:
    """Open a ThreatConnect session using PRISM config paths/params."""
    return ThreatConnectClient(
        config_path=config.config_path,
        tc_sdk_path=config.tc_sdk_path,
        tc_project_root=config.tc_project_root,
        result_page_size=config.result_page_size,
    )


__all__ = ["ThreatConnectClient", "connect_threatconnect", "load_api_config"]
