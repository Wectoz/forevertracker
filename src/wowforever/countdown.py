"""Launch countdown banner text."""

from datetime import UTC, datetime

LAUNCH = datetime(2026, 11, 4, 22, 0, tzinfo=UTC)  # Nov 4, 3:00 p.m. PDT


def launch_banner(now: datetime) -> str:
    if now >= LAUNCH:
        return "Live since Nov 4"
    days = (LAUNCH.date() - now.astimezone(UTC).date()).days
    if days <= 0:
        return "Launches today · Nov 4, 3:00 p.m. PDT"
    return f"Launches Nov 4 · {days} day{'s' if days != 1 else ''} to go"
