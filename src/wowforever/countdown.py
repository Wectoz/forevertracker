"""Launch countdown banner text."""

from datetime import UTC, datetime

LAUNCH = datetime(2026, 11, 4, 23, 0, tzinfo=UTC)  # Nov 4, 3:00 p.m. PST (DST ends Nov 1)


def launch_banner(now: datetime) -> str:
    if now >= LAUNCH:
        return "Live since Nov 4"
    days = (LAUNCH.date() - now.astimezone(UTC).date()).days
    if days <= 0:
        return "Launches today · Nov 4, 3:00 p.m. PST"
    return f"Launches Nov 4 · {days} day{'s' if days != 1 else ''} to go"


def time_left(now: datetime) -> tuple[int, int, int] | None:
    """(days, hours, minutes) until launch, or None once it has launched."""
    if now >= LAUNCH:
        return None
    minutes = int((LAUNCH - now).total_seconds() // 60)
    return minutes // 1440, minutes % 1440 // 60, minutes % 60
