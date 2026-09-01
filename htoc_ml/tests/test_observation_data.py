from htoc_ml.core.observations import ObservationData


def test_groupby_sort_false_preserves_first_seen_order(synthetic_observation_frame):
    observations = ObservationData.from_frame(synthetic_observation_frame)
    keys = list(observations.labels.items())
    assert keys[0][0] == ("FDA", "daily.example")
    assert observations.labels.seen_next(
        keys[0][1], cutoff_day=int(synthetic_observation_frame["d"].max()) - 1, horizon_days=1
    ) in (0, 1)
    assert observations.features is observations.labels
    assert observations.labels.opdivs() == ["CMS", "FDA"]
