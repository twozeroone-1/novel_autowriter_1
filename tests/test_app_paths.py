import unittest
from pathlib import Path

from core.app_paths import APP_ROOT, DATA_PROJECTS_DIR, ENV_FILE_PATH


class TestAppPaths(unittest.TestCase):
    def test_app_paths_are_absolute_and_rooted(self):
        self.assertTrue(APP_ROOT.is_absolute())
        self.assertEqual(DATA_PROJECTS_DIR, APP_ROOT / "data" / "projects")
        self.assertEqual(ENV_FILE_PATH, APP_ROOT / ".env")

    def test_app_root_matches_repository_root(self):
        self.assertEqual(APP_ROOT, Path(__file__).resolve().parent.parent)


if __name__ == "__main__":
    unittest.main()
