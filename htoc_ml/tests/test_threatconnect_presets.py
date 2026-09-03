"""Tests for shared ThreatConnect preset lists."""
from htoc.core.threatconnect_presets import OWNERS_DAILY, OWNERS_WEEKLY
from htoc.prism.config import DAILY_OWNERS, WEEKLY_OWNERS


def test_prism_config_uses_shared_presets():
    assert WEEKLY_OWNERS == OWNERS_WEEKLY
    assert DAILY_OWNERS == OWNERS_DAILY
    assert "Intel471" in WEEKLY_OWNERS
    assert "Intel 471 Intelligence" in DAILY_OWNERS
