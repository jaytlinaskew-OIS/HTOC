"""Catch-the-sightings confidence bands. Policy values match the live V4 runner."""
from __future__ import annotations

BAND_LOW_P = 0.20
BAND_LABELS = {"H": "Highly likely", "W": "Possibly active", "L": "Low confidence"}

BAND_HIGH_P = {1: 0.80, 7: 0.80, 14: 0.80, 30: 0.80, 45: 0.80}

BAND_HIGH_P_OPDIV = {
    "CMS": {1: 0.65, 7: 0.65},
    "HRSA": {1: 0.75, 7: 0.70},
    "OS": {7: 0.65},
    "FDA": {7: 0.65},
    "HHS": {7: 0.65},
    "NIH": {7: 0.65},
    "VA": {7: 0.70},
    "CDC": {7: 0.70},
}

PROBNAME = {
    1: "Probability: 1-Day",
    7: "Probability: 7-Day",
    14: "Probability: 14-Day",
    30: "Probability: 30-Day",
    45: "Probability: 45-Day",
}
CONFNAME = {
    1: "Confidence: 1-Day",
    7: "Confidence: 7-Day",
    14: "Confidence: 14-Day",
    30: "Confidence: 30-Day",
    45: "Confidence: 45-Day",
}


class BandPolicy:
    def __init__(
        self,
        high_by_horizon: dict[int, float] | None = None,
        high_by_opdiv: dict[str, dict[int, float]] | None = None,
        low: float = BAND_LOW_P,
    ) -> None:
        self.high_by_horizon = high_by_horizon or dict(BAND_HIGH_P)
        self.high_by_opdiv = high_by_opdiv or {k: dict(v) for k, v in BAND_HIGH_P_OPDIV.items()}
        self.low = low

    def high_cut(self, horizon_days: int, opdiv: str | None = None) -> float:
        h = int(horizon_days)
        if opdiv is not None:
            by_h = self.high_by_opdiv.get(str(opdiv).strip().upper())
            if by_h and h in by_h:
                return float(by_h[h])
        return float(self.high_by_horizon.get(h, 0.80))

    def label(self, probability: float, horizon_days: int, opdiv: str | None = None) -> str:
        try:
            p = float(probability)
        except (TypeError, ValueError):
            return BAND_LABELS["W"]
        if p >= self.high_cut(horizon_days, opdiv):
            return BAND_LABELS["H"]
        if p <= self.low:
            return BAND_LABELS["L"]
        return BAND_LABELS["W"]
