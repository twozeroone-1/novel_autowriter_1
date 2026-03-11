import importlib
import importlib.util
import unittest
from datetime import datetime, timezone


class TestAutomationScheduler(unittest.TestCase):
    def _load_scheduler(self):
        spec = importlib.util.find_spec("core.automation_scheduler")
        self.assertIsNotNone(spec, "core.automation_scheduler should exist")
        module = importlib.import_module("core.automation_scheduler")
        is_schedule_due = getattr(module, "is_schedule_due", None)
        self.assertIsNotNone(is_schedule_due, "is_schedule_due should exist")
        return is_schedule_due

    def test_daily_schedule_matches_target_minute(self):
        is_schedule_due = self._load_scheduler()

        now = datetime(2026, 3, 12, 21, 0, tzinfo=timezone.utc)
        rule = {"type": "daily", "time": "21:00"}

        self.assertTrue(is_schedule_due(rule, now=now, last_run_at=None))

    def test_weekly_schedule_matches_named_weekday(self):
        is_schedule_due = self._load_scheduler()

        now = datetime(2026, 3, 13, 7, 30, tzinfo=timezone.utc)
        rule = {"type": "weekly", "time": "07:30", "days": ["fri"]}

        self.assertTrue(is_schedule_due(rule, now=now, last_run_at=None))

    def test_interval_schedule_uses_last_success_time(self):
        is_schedule_due = self._load_scheduler()

        now = datetime(2026, 3, 12, 12, 0, tzinfo=timezone.utc)
        rule = {"type": "interval", "hours": 6}
        last_run_at = "2026-03-12T06:00:00+00:00"

        self.assertTrue(is_schedule_due(rule, now=now, last_run_at=last_run_at))

    def test_same_minute_last_run_blocks_duplicate_trigger(self):
        is_schedule_due = self._load_scheduler()

        now = datetime(2026, 3, 12, 21, 0, 30, tzinfo=timezone.utc)
        rule = {"type": "daily", "time": "21:00"}
        last_run_at = "2026-03-12T21:00:00+00:00"

        self.assertFalse(is_schedule_due(rule, now=now, last_run_at=last_run_at))


if __name__ == "__main__":
    unittest.main()
