"""Explicit daily reset instants. Missing/ambiguous time never silently selects a reset."""

from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from packages.risk.contracts import PolicyTerms


def reset_instant(day: date, policy: PolicyTerms) -> datetime:
    zone = ZoneInfo(policy.timezone)
    naive = datetime.combine(day, time(policy.reset_minute // 60, policy.reset_minute % 60))
    candidates = []
    for fold in (0, 1):
        aware = naive.replace(tzinfo=zone, fold=fold)
        utc = aware.astimezone(UTC)
        if utc.astimezone(zone).replace(tzinfo=None) == naive:
            candidates.append(utc)
    if not candidates:
        raise ValueError("NONEXISTENT_DAILY_RESET_TIME")
    return min(candidates) if policy.reset_fold == "EARLIER" else max(candidates)


def period_start(at: datetime, policy: PolicyTerms) -> datetime:
    day = at.astimezone(ZoneInfo(policy.timezone)).date()
    instant = reset_instant(day, policy)
    return instant if instant <= at else reset_instant(day - timedelta(days=1), policy)
