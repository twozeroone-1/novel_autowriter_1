import tempfile
import unittest
from pathlib import Path

from core.file_utils import remove_env_key, remove_env_key_contents, update_env_file, upsert_env_contents


class TestFileUtils(unittest.TestCase):
    def test_upsert_env_contents_appends_new_key(self):
        updated = upsert_env_contents("FOO=\"bar\"\n", "BAZ", "qux")
        self.assertEqual(updated, 'FOO="bar"\nBAZ="qux"\n')

    def test_upsert_env_contents_replaces_existing_key_and_escapes_quotes(self):
        updated = upsert_env_contents('FOO="bar"\nBAZ="old"\n', "BAZ", 'new"value')
        self.assertEqual(updated, 'FOO="bar"\nBAZ="new\\"value"\n')

    def test_update_env_file_creates_new_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env"

            update_env_file(env_path, "FOO", "bar")

            self.assertEqual(env_path.read_text(encoding="utf-8"), 'FOO="bar"\n')

    def test_update_env_file_replaces_existing_key_in_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env"
            env_path.write_text('FOO="old"\nBAR="keep"\n', encoding="utf-8")

            update_env_file(env_path, "FOO", "new")

            self.assertEqual(env_path.read_text(encoding="utf-8"), 'FOO="new"\nBAR="keep"\n')

    def test_upsert_env_contents_preserves_windows_line_endings(self):
        updated = upsert_env_contents('FOO="bar"\r\n', "BAZ", "qux")
        self.assertEqual(updated, 'FOO="bar"\r\nBAZ="qux"\r\n')

    def test_remove_env_key_contents_removes_target_key(self):
        updated = remove_env_key_contents('FOO="bar"\nBAZ="qux"\n', "FOO")
        self.assertEqual(updated, 'BAZ="qux"\n')

    def test_remove_env_key_updates_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env"
            env_path.write_text('FOO="bar"\nBAZ="qux"\n', encoding="utf-8")

            remove_env_key(env_path, "FOO")

            self.assertEqual(env_path.read_text(encoding="utf-8"), 'BAZ="qux"\n')


if __name__ == "__main__":
    unittest.main()
