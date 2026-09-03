from datetime import date

from htoc.core.day import to_date, to_day_index, to_timestamp


def test_epoch_round_trip():
    day = to_day_index(date(2026, 8, 26))
    assert to_date(int(day)) == date(2026, 8, 26)
    assert to_timestamp(int(day)).date() == date(2026, 8, 26)


def test_known_epoch_offset():
    assert int(to_day_index(date(2020, 1, 1))) == 0
    assert int(to_day_index(date(2020, 1, 2))) == 1
