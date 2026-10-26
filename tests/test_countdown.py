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
    assert launch_banner(at(2026, 11, 4, 23)) == "Live since Nov 4"
    assert launch_banner(at(2026, 12, 1)) == "Live since Nov 4"
