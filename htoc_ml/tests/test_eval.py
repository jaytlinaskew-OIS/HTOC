import pandas as pd

from htoc.core.eval.alerts import MetricAlertRule, collect_alerts
from htoc.core.eval.metrics import (
    NOT_APPLICABLE,
    BandSpec,
    count_bands,
    percent_or_sentinel,
    rates_from_counts,
)
from htoc.core.eval.workbook import traffic_light_for_value, upsert_history


SPEC = BandSpec(positive_name="Highly likely", negative_name="Low confidence", abstain_name="Possibly active")


def _frame(rows):
    return pd.DataFrame(rows, columns=["band", "observed", "indicator"])


def test_high_class_accuracy_excludes_true_negatives():
    rows = (
        [{"band": "Highly likely", "observed": 1, "indicator": f"h{i}"} for i in range(11)]
        + [{"band": "Low confidence", "observed": 1, "indicator": f"fn{i}"} for i in range(9)]
        + [{"band": "Low confidence", "observed": 0, "indicator": f"tn{i}"} for i in range(186)]
    )
    counts = count_bands(_frame(rows), prediction_col="band", label_col="observed", spec=SPEC, unique_col="indicator")
    rates = rates_from_counts(counts)
    assert counts.true_positive == 11
    assert counts.missed_positive == 9
    assert counts.true_negative == 186
    assert round(rates.accuracy_positive, 4) == round(11 / 20, 4)
    assert round(rates.accuracy, 4) == round(197 / 206, 4)
    assert percent_or_sentinel(rates.accuracy_positive, rates.accuracy_positive_defined) == 55.0


def test_custom_band_names_for_another_classifier():
    spec = BandSpec(positive_name="malicious", negative_name="benign", abstain_name="hold")
    frame = pd.DataFrame(
        {
            "call": ["malicious", "malicious", "benign", "hold"],
            "label": [1, 0, 0, 1],
        }
    )
    counts = count_bands(frame, prediction_col="call", label_col="label", spec=spec)
    rates = rates_from_counts(counts)
    assert counts.true_positive == 1
    assert counts.false_positive == 1
    assert counts.true_negative == 1
    assert counts.abstain_ended_positive == 1
    assert round(rates.recall_all, 4) == 0.5


def test_empty_positive_band_is_not_applicable():
    rows = [{"band": "Low confidence", "observed": 1, "indicator": "a"}]
    rates = rates_from_counts(
        count_bands(_frame(rows), prediction_col="band", label_col="observed", spec=SPEC)
    )
    assert percent_or_sentinel(rates.precision, rates.precision_defined) == NOT_APPLICABLE


def test_no_positives_blanks_accuracy_and_negative_precision():
    rows = [{"band": "Low confidence", "observed": 0, "indicator": "a"}]
    rates = rates_from_counts(
        count_bands(_frame(rows), prediction_col="band", label_col="observed", spec=SPEC)
    )
    assert percent_or_sentinel(rates.accuracy, rates.accuracy_defined) == NOT_APPLICABLE
    assert percent_or_sentinel(rates.negative_precision, rates.negative_precision_defined) == NOT_APPLICABLE


def test_abstain_positives_count_in_recall_all_only():
    rows = [
        {"band": "Highly likely", "observed": 1, "indicator": "tp"},
        {"band": "Low confidence", "observed": 1, "indicator": "fn"},
        {"band": "Possibly active", "observed": 1, "indicator": "pa"},
    ]
    rates = rates_from_counts(
        count_bands(_frame(rows), prediction_col="band", label_col="observed", spec=SPEC)
    )
    assert round(rates.recall_decided, 4) == 0.5
    assert round(rates.recall_all, 4) == round(1 / 3, 4)


def test_precision_drop_alert_only_fires_under_floor():
    rule = MetricAlertRule(
        raw_column="_raw_precision",
        n_column="Decided (High + Low)",
        min_n=10,
        abs_min=0.90,
        drop_pp=0.05,
        rolling_days=2,
        drop_only_when_below_floor=True,
        floor_template="floor {value}",
        drop_template="drop {value}",
    )
    history = pd.DataFrame({"_raw_precision": [0.95, 0.94]})
    under = {"_raw_precision": 0.80, "Decided (High + Low)": 50}
    over = {"_raw_precision": 0.92, "Decided (High + Low)": 50}
    under_alerts = collect_alerts(history, under, [rule], tag="1-Day")
    over_alerts = collect_alerts(history, over, [rule], tag="1-Day")
    assert any("floor" in line for line in under_alerts)
    assert any("drop" in line for line in under_alerts)
    assert over_alerts == []


def test_provisional_rows_are_not_alerted():
    from htoc.noi.eval.config import EvalConfig
    from htoc.noi.eval.runner import PerformanceEval

    evaler = PerformanceEval(EvalConfig.from_paths(".", "."))
    row = {
        "Data Status": "Scored (provisional - scored before the label window settled)",
        "Horizon (Days)": 1,
        "_raw_precision": 0.1,
        "Decided (High + Low)": 100,
        "Actual Positives": 10,
    }
    assert evaler.maybe_alert(pd.DataFrame(), row) == []


def test_upsert_keeps_latest_row():
    existing = pd.DataFrame(
        [{"Evaluation Date": "20260820", "Horizon (Days)": "1", "Actual Positives": 1}]
    )
    newer = [{"Evaluation Date": "20260820", "Horizon (Days)": "1", "Actual Positives": 9}]
    out = upsert_history(
        existing,
        newer,
        keys=["Evaluation Date", "Horizon (Days)"],
        columns=["Evaluation Date", "Horizon (Days)", "Actual Positives"],
        sort_by=["Evaluation Date"],
    )
    assert len(out) == 1
    assert int(out["Actual Positives"].iloc[0]) == 9


def test_traffic_light_thresholds():
    green, _ = traffic_light_for_value(90.0, 90.0, 85.0)
    yellow, _ = traffic_light_for_value(85.0, 90.0, 85.0)
    red, _ = traffic_light_for_value(80.0, 90.0, 85.0)
    assert green.fgColor.rgb[-6:] == "C6EFCE"
    assert yellow.fgColor.rgb[-6:] == "FFEB9C"
    assert red.fgColor.rgb[-6:] == "FFC7CE"
    assert traffic_light_for_value("Missing Data to compute", 90.0, 85.0) is None
