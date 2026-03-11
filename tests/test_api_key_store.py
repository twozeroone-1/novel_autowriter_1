import os
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.api_key_store import (
    delete_api_key_from_secure_storage,
    env_file_has_key,
    get_secure_api_key,
    has_secure_storage,
    load_secure_api_key_into_environment,
    save_api_key_to_secure_storage,
)


class FakeKeyringBackend:
    pass


class FakeFailBackend:
    pass


FakeFailBackend.__module__ = "keyring.backends.fail"


class FakeKeyring:
    def __init__(self):
        self.store = {}
        self.backend = FakeKeyringBackend()

    def get_keyring(self):
        return self.backend

    def get_password(self, service_name, account_name):
        return self.store.get((service_name, account_name))

    def set_password(self, service_name, account_name, value):
        self.store[(service_name, account_name)] = value

    def delete_password(self, service_name, account_name):
        self.store.pop((service_name, account_name), None)


class TestApiKeyStore(unittest.TestCase):
    def test_has_secure_storage_false_for_fail_backend(self):
        fake_keyring = FakeKeyring()
        fake_keyring.backend = FakeFailBackend()

        with patch("core.api_key_store.keyring", fake_keyring):
            self.assertFalse(has_secure_storage())

    def test_save_api_key_to_secure_storage_removes_plaintext_env_key(self):
        fake_keyring = FakeKeyring()
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env"
            env_path.write_text('GOOGLE_API_KEY="plain"\n', encoding="utf-8")

            with patch("core.api_key_store.keyring", fake_keyring):
                ok, message = save_api_key_to_secure_storage("secret-key", env_path=env_path)

            self.assertTrue(ok)
            self.assertIn("보안 저장소", message)
            self.assertEqual(fake_keyring.store[("novel-autowriter", "google_api_key")], "secret-key")
            self.assertFalse(env_file_has_key(env_path))

    def test_load_secure_api_key_into_environment_sets_runtime_value(self):
        fake_keyring = FakeKeyring()
        fake_keyring.store[("novel-autowriter", "google_api_key")] = "secure-key"

        with patch("core.api_key_store.keyring", fake_keyring), patch.dict(os.environ, {}, clear=True):
            loaded = load_secure_api_key_into_environment()
            self.assertTrue(loaded)
            self.assertEqual(os.environ["GOOGLE_API_KEY"], "secure-key")

    def test_delete_api_key_from_secure_storage(self):
        fake_keyring = FakeKeyring()
        fake_keyring.store[("novel-autowriter", "google_api_key")] = "secure-key"

        with patch("core.api_key_store.keyring", fake_keyring):
            ok, message = delete_api_key_from_secure_storage()

        self.assertTrue(ok)
        self.assertIn("삭제", message)
        self.assertEqual(fake_keyring.store, {})


if __name__ == "__main__":
    unittest.main()
