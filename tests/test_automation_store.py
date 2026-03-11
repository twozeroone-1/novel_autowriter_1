import importlib
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class TestAutomationStore(unittest.TestCase):
    def test_load_automation_config_returns_defaults_when_missing(self):
        spec = importlib.util.find_spec("core.automation_store")
        self.assertIsNotNone(spec, "core.automation_store should exist")
        module = importlib.import_module("core.automation_store")
        store_cls = getattr(module, "AutomationStore", None)
        self.assertIsNotNone(store_cls, "AutomationStore should exist")

        with tempfile.TemporaryDirectory() as tmpdir:
            projects_dir = Path(tmpdir) / "projects"
            with patch.object(module, "DATA_PROJECTS_DIR", projects_dir):
                store = store_cls(project_name="sample")
                config = store.load_config()

        self.assertFalse(config["enabled"])
        self.assertEqual(config["schedule"]["type"], "daily")


if __name__ == "__main__":
    unittest.main()
