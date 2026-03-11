import subprocess
import unittest
from unittest.mock import patch

from core.llm_backend import (
    CliAuthError,
    CliUnavailableError,
    GeminiCliBackend,
    LlmBackendResult,
    LlmRequest,
    compose_cli_prompt,
    find_gemini_cli_executable,
    generate_via_backend_mode,
    resolve_backend_mode,
)


class FakeBackend:
    def __init__(self, text: str | None = None, error: Exception | None = None, backend_used: str = "api"):
        self.text = text
        self.error = error
        self.backend_used = backend_used
        self.requests: list[LlmRequest] = []

    def generate(self, request: LlmRequest) -> LlmBackendResult:
        self.requests.append(request)
        if self.error:
            raise self.error
        return LlmBackendResult(text=self.text or "", backend_used=self.backend_used, diagnostics=())


class TestLlmBackends(unittest.TestCase):
    def setUp(self):
        self.request = LlmRequest(
            prompt="prompt body",
            system_instruction="system note",
            temperature=0.2,
            model_name="gemini-2.5-flash",
        )

    def test_resolve_backend_mode_uses_auto_as_default(self):
        self.assertEqual(resolve_backend_mode(None), "auto")
        self.assertEqual(resolve_backend_mode(""), "auto")
        self.assertEqual(resolve_backend_mode("unknown"), "auto")

    def test_resolve_backend_mode_accepts_api_and_cli(self):
        self.assertEqual(resolve_backend_mode("api"), "api")
        self.assertEqual(resolve_backend_mode("cli"), "cli")
        self.assertEqual(resolve_backend_mode("AUTO"), "auto")

    @patch("core.llm_backend.shutil.which")
    def test_find_gemini_cli_executable_prefers_cmd_on_windows(self, mocked_which):
        mocked_which.side_effect = lambda name: {
            "gemini.cmd": r"C:\Users\W\AppData\Roaming\npm\gemini.cmd",
            "gemini": None,
        }.get(name)

        self.assertEqual(
            find_gemini_cli_executable("win32"),
            r"C:\Users\W\AppData\Roaming\npm\gemini.cmd",
        )

    def test_compose_cli_prompt_includes_system_instruction_block(self):
        prompt = compose_cli_prompt("user body", system_instruction="system note")

        self.assertIn("System instruction:", prompt)
        self.assertIn("system note", prompt)
        self.assertIn("User request:", prompt)
        self.assertIn("user body", prompt)

    @patch("core.llm_backend.subprocess.run")
    def test_gemini_cli_backend_returns_stdout_text(self, mocked_run):
        mocked_run.return_value = subprocess.CompletedProcess(
            args=["gemini.cmd"],
            returncode=0,
            stdout="generated text\n",
            stderr="",
        )

        backend = GeminiCliBackend(executable_path="gemini.cmd", timeout_seconds=10)
        result = backend.generate(self.request)

        self.assertEqual(result.text, "generated text")
        self.assertEqual(result.backend_used, "cli")
        command = mocked_run.call_args.args[0]
        self.assertIn("--prompt", command)
        self.assertEqual(command[command.index("--prompt") + 1], "")
        self.assertEqual(
            mocked_run.call_args.kwargs["input"],
            compose_cli_prompt("prompt body", "system note"),
        )

    def test_auto_backend_falls_back_to_api_when_cli_unavailable(self):
        cli_backend = FakeBackend(error=CliUnavailableError("missing"), backend_used="cli")
        api_backend = FakeBackend(text="api text", backend_used="api")

        result = generate_via_backend_mode(
            "auto",
            self.request,
            cli_backend=cli_backend,
            api_backend=api_backend,
        )

        self.assertEqual(result.text, "api text")
        self.assertEqual(result.backend_used, "api")
        self.assertIn("missing", " ".join(result.diagnostics))
        self.assertEqual(len(cli_backend.requests), 1)
        self.assertEqual(len(api_backend.requests), 1)

    def test_cli_mode_does_not_fallback_to_api(self):
        cli_backend = FakeBackend(error=CliAuthError("not logged in"), backend_used="cli")
        api_backend = FakeBackend(text="api text", backend_used="api")

        with self.assertRaises(CliAuthError):
            generate_via_backend_mode(
                "cli",
                self.request,
                cli_backend=cli_backend,
                api_backend=api_backend,
            )

        self.assertEqual(len(cli_backend.requests), 1)
        self.assertEqual(len(api_backend.requests), 0)


if __name__ == "__main__":
    unittest.main()
