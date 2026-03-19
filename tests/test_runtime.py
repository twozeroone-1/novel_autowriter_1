import os
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from core import runtime
from core.github_storage import GitHubProjectStorage
from core.storage import LocalProjectStorage, build_project_storage


class TestRuntime(unittest.TestCase):
    def test_get_runtime_mode_defaults_to_local(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(runtime.get_runtime_mode(), "local")

    def test_get_runtime_mode_reads_community_cloud_env(self):
        with patch.dict(os.environ, {"APP_RUNTIME": "community_cloud"}, clear=True):
            self.assertEqual(runtime.get_runtime_mode(), "community_cloud")

    def test_is_cloud_runtime_true_only_for_community_cloud(self):
        with patch.dict(os.environ, {"APP_RUNTIME": "community_cloud"}, clear=True):
            self.assertTrue(runtime.is_cloud_runtime())

        with patch.dict(os.environ, {"APP_RUNTIME": "local"}, clear=True):
            self.assertFalse(runtime.is_cloud_runtime())

    def test_validate_cloud_storage_settings_raises_when_missing(self):
        with patch.dict(os.environ, {"APP_RUNTIME": "community_cloud"}, clear=True):
            with self.assertRaises(RuntimeError):
                runtime.validate_cloud_storage_settings()

    def test_validate_cloud_storage_settings_accepts_complete_configuration(self):
        with patch.dict(
            os.environ,
            {
                "APP_RUNTIME": "community_cloud",
                "GITHUB_STORAGE_REPO": "owner/repo",
                "GITHUB_STORAGE_TOKEN": "secret-token",
            },
            clear=True,
        ):
            runtime.validate_cloud_storage_settings()

    def test_build_project_storage_defaults_to_local_backend(self):
        with patch.dict(os.environ, {}, clear=True):
            storage = build_project_storage(Path("C:/tmp/projects"))

        self.assertIsInstance(storage, LocalProjectStorage)

    def test_build_project_storage_returns_github_backend_in_cloud_mode(self):
        with patch.dict(
            os.environ,
            {
                "APP_RUNTIME": "community_cloud",
                "GITHUB_STORAGE_REPO": "owner/repo",
                "GITHUB_STORAGE_TOKEN": "secret-token",
            },
            clear=True,
        ):
            storage = build_project_storage(Path("C:/tmp/projects"))

        self.assertIsInstance(storage, GitHubProjectStorage)

    def test_load_streamlit_secrets_into_environment_sets_missing_values(self):
        fake_streamlit = types.SimpleNamespace(
            secrets={
                "GOOGLE_API_KEY": "secret-from-streamlit",
                "GITHUB_STORAGE_REPO": "owner/repo",
            }
        )

        with patch.dict(sys.modules, {"streamlit": fake_streamlit}, clear=False):
            with patch.dict(os.environ, {}, clear=True):
                loaded = runtime.load_streamlit_secrets_into_environment()
                self.assertTrue(loaded)
                self.assertEqual(os.environ["GOOGLE_API_KEY"], "secret-from-streamlit")
                self.assertEqual(os.environ["GITHUB_STORAGE_REPO"], "owner/repo")

    def test_load_streamlit_secrets_into_environment_preserves_existing_env(self):
        fake_streamlit = types.SimpleNamespace(
            secrets={
                "GOOGLE_API_KEY": "secret-from-streamlit",
            }
        )

        with patch.dict(sys.modules, {"streamlit": fake_streamlit}, clear=False):
            with patch.dict(os.environ, {"GOOGLE_API_KEY": "already-set"}, clear=True):
                runtime.load_streamlit_secrets_into_environment()
                self.assertEqual(os.environ["GOOGLE_API_KEY"], "already-set")


if __name__ == "__main__":
    unittest.main()
