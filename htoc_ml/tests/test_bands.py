from htoc.noi.bands import BandPolicy


def test_default_high_cut_is_080():
    policy = BandPolicy()
    assert policy.high_cut(1) == 0.80
    assert policy.label(0.80, 1) == "Highly likely"
    assert policy.label(0.20, 1) == "Low confidence"
    assert policy.label(0.50, 1) == "Possibly active"


def test_per_opdiv_high_cuts():
    policy = BandPolicy()
    assert policy.high_cut(1, "CMS") == 0.65
    assert policy.high_cut(7, "VA") == 0.70
    assert policy.high_cut(1, "VA") == 0.80
    assert policy.label(0.66, 1, "CMS") == "Highly likely"
    assert policy.label(0.66, 1, "CDC") == "Possibly active"
