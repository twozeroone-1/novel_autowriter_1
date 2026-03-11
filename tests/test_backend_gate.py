import unittest

from core.llm_backend import GeminiCliStatus, get_backend_gate_error


class TestBackendGate(unittest.TestCase):
    def test_api_mode_requires_api_key(self):
        error = get_backend_gate_error(
            "api",
            has_api_key=False,
            cli_status=GeminiCliStatus(available=True, path="gemini.cmd", authenticated=True),
        )

        self.assertIsNotNone(error)
        self.assertIn("API", error)

    def test_cli_mode_allows_available_cli_without_api_key(self):
        error = get_backend_gate_error(
            "cli",
            has_api_key=False,
            cli_status=GeminiCliStatus(available=True, path="gemini.cmd", authenticated=None),
        )

        self.assertIsNone(error)

    def test_cli_mode_requires_authenticated_cli(self):
        error = get_backend_gate_error(
            "cli",
            has_api_key=False,
            cli_status=GeminiCliStatus(available=True, path="gemini.cmd", authenticated=False),
        )

        self.assertIsNotNone(error)
        self.assertIn("Gemini CLI", error)
        self.assertIn("OAuth", error)

    def test_auto_mode_allows_available_cli_without_api_key(self):
        error = get_backend_gate_error(
            "auto",
            has_api_key=False,
            cli_status=GeminiCliStatus(available=True, path="gemini.cmd", authenticated=None),
        )

        self.assertIsNone(error)

    def test_auto_mode_requires_api_key_or_cli(self):
        error = get_backend_gate_error(
            "auto",
            has_api_key=False,
            cli_status=GeminiCliStatus(available=False, path=None, authenticated=None),
        )

        self.assertIsNotNone(error)
        self.assertIn("API", error)
        self.assertIn("Gemini CLI", error)


if __name__ == "__main__":
    unittest.main()
