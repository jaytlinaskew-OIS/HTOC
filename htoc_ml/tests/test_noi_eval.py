import pandas as pd

from htoc_ml.core.eval.metrics import NOT_APPLICABLE
from htoc_ml.noi.eval.scoring import score_banded_forecast, week_horizon_coverage


def test_score_banded_forecast_maps_bands_and_week_coverage():
    predictions = pd.DataFrame(
        {
            "Indicator": ["a", "b", "c", "d"],
            "Partner": ["CDC", "CDC", "CDC", "CDC"],
            "Confidence: 1-Day": [
                "1-Day: Highly likely",
                "1-Day: Low confidence",
                "1-Day: Possibly active",
                "1-Day: Highly likely",
            ],
            "Confidence: 7-Day": [
                "7-Day: Highly likely",
                "7-Day: Low confidence",
                "7-Day: Highly likely",
                "7-Day: Low confidence",
            ],
            "Probability: 1-Day": ["90%", "10%", "50%", "85%"],
        }
    )
    observations = pd.DataFrame(
        {
            "Indicator": ["a", "c"],
            "Partner": ["CDC", "CDC"],
            "Observed": [1, 1],
        }
    )
    row = score_banded_forecast(
        predictions,
        observations,
        horizon_days=1,
        eval_date_str="20260828",
        forecast_date_str="20260827",
        excluded_info={},
        provisional_info={},
        excluded_pairs=0,
        excluded_pop={},
    )
    assert row["True Positives (High)"] == 1
    assert row["False Positives (High)"] == 1
    assert row["False Negatives (High)"] == 0
    assert row["Possibly Active Ended High (Observed)"] == 1
    assert row["Actual Positives"] == 2
    assert row["Recall - High vs All Positives (%)"] == 50.0
    assert row["Possibly Active Observed already 7-Day High"] == 1
    assert row["Recall - 7-Day High vs 1-Day Positives (%)"] == 100.0
    opdiv = row["_opdiv_rows"][0]
    assert opdiv["OpDiv"] == "CDC"


def test_week_coverage_is_na_off_1day():
    frame = pd.DataFrame(
        {
            "Observed": [1],
            "band_h": ["Highly likely"],
            "band_7": ["Highly likely"],
        }
    )
    out = week_horizon_coverage(frame, 7)
    assert out["recall_7d"] == NOT_APPLICABLE
