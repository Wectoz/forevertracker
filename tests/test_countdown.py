from datetime import UTC, datetime

from wowforever.countdown import launch_banner


def at(*args):
    return datetime(*args, tzinfo=UTC)


def test_days_to_go():
    assert launch_banner(at(2026, 10, 26, 12)) == "Launches Nov 4 · 9 days to go"


def test_one_day_to_go():
    assert launch_banner(at(2026, 11, 3, 12)) == "Launches Nov 4 · 1 day to go"


def test_launch_day_before_launch():
    assert launch_banner(at(2026, 11, 4, 10)) == "Launches today · Nov 4, 3:00 p.m. PST"


def test_live_after_launch():
    assert launch_banner(at(2026, 11, 4, 22, 30)) == "Launches today · Nov 4, 3:00 p.m. PST"
    assert launch_banner(at(2026, 11, 4, 23)) == "Live now · Day 1"
    # Days roll over at midnight Pacific: 07:59 UTC on Nov 6 is still Nov 5 in California.
    assert launch_banner(at(2026, 11, 6, 7, 59)) == "Live now · Day 2"
    assert launch_banner(at(2026, 11, 6, 8)) == "Live now · Day 3"


def test_time_left_splits_days_hours_minutes():
    from wowforever.countdown import time_left
    assert time_left(at(2026, 10, 26, 12)) == (9, 11, 0)
    assert time_left(at(2026, 11, 4, 22, 30)) == (0, 0, 30)
    assert time_left(at(2026, 11, 4, 23)) is None
