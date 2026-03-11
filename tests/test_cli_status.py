import subprocess
import unittest
from unittest.mock import patch

from core.llm_backend import GeminiCliStatus, probe_gemini_cli
from ui.workspace import format_cli_status


class TestCliStatus(unittest.TestCase):
    def test_format_cli_status_reports_installed_but_untested(self):
        status = GeminiCliStatus(
            available=True,
            path=r"C:\Users\W\AppData\Roaming\npm\gemini.cmd",
            version="0.10.0",
            authenticated=None,
            message="Gemini CLI is installed.",
        )

        self.assertIn("설치됨", format_cli_status(status))
        self.assertIn("테스트 필요", format_cli_status(status))

    def test_format_cli_status_reports_auth_ready(self):
        status = GeminiCliStatus(
            available=True,
            path=r"C:\Users\W\AppData\Roaming\npm\gemini.cmd",
            version="0.10.0",
            authenticated=True,
            message="Gemini CLI connection test succeeded.",
        )

        self.assertIn("OAuth 사용 가능", format_cli_status(status))

    def test_format_cli_status_reports_login_required(self):
        status = GeminiCliStatus(
            available=True,
            path=r"C:\Users\W\AppData\Roaming\npm\gemini.cmd",
            version="0.10.0",
            authenticated=False,
            message="Authentication is required.",
        )

        self.assertIn("로그인 필요", format_cli_status(status))

    @patch("core.llm_backend.find_gemini_cli_executable", return_value=None)
    def test_probe_gemini_cli_returns_missing_status_when_executable_absent(self, _mocked_find):
        status = probe_gemini_cli()

        self.assertFalse(status.available)
        self.assertIsNone(status.path)
        self.assertIsNone(status.version)

    @patch("core.llm_backend.find_gemini_cli_executable", return_value="gemini.cmd")
    @patch("core.llm_backend.subprocess.run")
    def test_probe_gemini_cli_reads_version(self, mocked_run, _mocked_find):
        mocked_run.return_value = subprocess.CompletedProcess(
            args=["gemini.cmd", "--version"],
            returncode=0,
            stdout="0.10.0\n",
            stderr="",
        )

        status = probe_gemini_cli()

        self.assertTrue(status.available)
        self.assertEqual(status.path, "gemini.cmd")
        self.assertEqual(status.version, "0.10.0")


if __name__ == "__main__":
    unittest.main()
