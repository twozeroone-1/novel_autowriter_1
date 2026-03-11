from datetime import datetime


WEEKDAY_NAMES = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def is_schedule_due(rule: dict, now: datetime, last_run_at: str | None) -> bool:
    last_run = _parse_datetime(last_run_at)
    if _same_minute(now, last_run):
        return False

    schedule_type = rule.get("type", "daily")
    if schedule_type == "daily":
        return _matches_time(rule.get("time", "00:00"), now)
    if schedule_type == "weekly":
        allowed_days = {str(day).strip().lower() for day in rule.get("days", [])}
        return WEEKDAY_NAMES[now.weekday()] in allowed_days and _matches_time(rule.get("time", "00:00"), now)
    if schedule_type == "interval":
        if last_run is None:
            return True
        hours = int(rule.get("hours", 24))
        elapsed_seconds = (now - last_run).total_seconds()
        return elapsed_seconds >= hours * 3600
    return False


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


def _same_minute(now: datetime, last_run: datetime | None) -> bool:
    if last_run is None:
        return False
    return now.replace(second=0, microsecond=0) == last_run.replace(second=0, microsecond=0)


def _matches_time(raw_time: str, now: datetime) -> bool:
    hour_text, minute_text = raw_time.split(":", maxsplit=1)
    return now.hour == int(hour_text) and now.minute == int(minute_text)
