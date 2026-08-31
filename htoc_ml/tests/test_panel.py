from htoc_ml.core.observations import ObservationPanel


def test_groupby_sort_false_preserves_first_seen_order(synthetic_panel):
    panel = ObservationPanel.from_frame(synthetic_panel)
    keys = list(panel.labels.items())
    assert keys[0][0] == ("FDA", "daily.example")
    assert panel.labels.seen_next(keys[0][1], cutoff_day=int(synthetic_panel["d"].max()) - 1, horizon_days=1) in (0, 1)
    assert panel.features is panel.labels
    assert panel.labels.opdivs() == ["CMS", "FDA"]
