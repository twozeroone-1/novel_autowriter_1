import unittest
from types import SimpleNamespace
from unittest.mock import patch

from core.llm import LLMError, _should_retry_on_error, generate_text
from core.llm_backend import LlmBackendResult


class FakeConfig:
    def __init__(self, temperature: float):
        self.temperature = temperature
        self.system_instruction = None


class FakeClient:
    def __init__(self, api_key: str, generate_content):
        self.api_key = api_key
        self.models = SimpleNamespace(generate_content=generate_content)


class FakeGenAI:
    def __init__(self, client_factory):
        self._client_factory = client_factory

    def Client(self, api_key: str):
        return self._client_factory(api_key)


class FakeApiError(Exception):
    def __init__(self, code: int, status: str, message: str):
        super().__init__(message)
        self.code = code
        self.status = status
        self.message = message


class FakeClientError(FakeApiError):
    pass


class FakeServerError(FakeApiError):
    pass


class FakeTimeoutException(Exception):
    pass


class FakeTransportError(Exception):
    pass


class TestLlmRetryPolicy(unittest.TestCase):
    def test_should_retry_on_error_prefers_typed_api_errors_and_network_errors(self):
        fake_errors = SimpleNamespace(
            APIError=FakeApiError,
            ClientError=FakeClientError,
            ServerError=FakeServerError,
        )
        fake_httpx = SimpleNamespace(
            TimeoutException=FakeTimeoutException,
            TransportError=FakeTransportError,
        )

        with patch("core.llm_backend.genai_errors", fake_errors), patch("core.llm_backend.httpx", fake_httpx):
            self.assertTrue(_should_retry_on_error(FakeServerError(503, "UNAVAILABLE", "server down")))
            self.assertTrue(_should_retry_on_error(FakeClientError(429, "RESOURCE_EXHAUSTED", "quota exhausted")))
            self.assertTrue(_should_retry_on_error(FakeTimeoutException("timed out")))
            self.assertFalse(_should_retry_on_error(FakeClientError(400, "INVALID_ARGUMENT", "bad prompt")))
            self.assertFalse(_should_retry_on_error(ValueError("bad prompt")))

    def test_generate_text_reads_backend_mode_from_environment(self):
        with patch(
            "core.llm.generate_via_backend_mode",
            return_value=LlmBackendResult(text="hello", backend_used="cli", diagnostics=()),
        ) as mocked_generate, patch.dict(
            "os.environ",
            {"GEMINI_BACKEND": "cli", "GEMINI_MODEL": "gemini-2.5-flash"},
            clear=True,
        ):
            result = generate_text("prompt body", system_instruction="system note", temperature=0.2)

        self.assertEqual(result, "hello")
        request = mocked_generate.call_args.args[1]
        self.assertEqual(mocked_generate.call_args.args[0], "cli")
        self.assertEqual(request.prompt, "prompt body")
        self.assertEqual(request.system_instruction, "system note")
        self.assertEqual(request.temperature, 0.2)
        self.assertEqual(request.model_name, "gemini-2.5-flash")

    def test_generate_text_retries_retryable_error_and_uses_second_key(self):
        call_log: list[tuple[str, str, str, float, str | None]] = []
        retryable_error = FakeClientError(429, "RESOURCE_EXHAUSTED", "quota exhausted")
        fake_errors = SimpleNamespace(
            APIError=FakeApiError,
            ClientError=FakeClientError,
            ServerError=FakeServerError,
        )

        def client_factory(api_key: str):
            def generate_content(*, model, contents, config):
                call_log.append((api_key, model, contents, config.temperature, config.system_instruction))
                if api_key == "key1":
                    raise retryable_error
                return SimpleNamespace(text="success text")

            return FakeClient(api_key, generate_content)

        fake_types = SimpleNamespace(GenerateContentConfig=FakeConfig)
        fake_genai = FakeGenAI(client_factory)

        with patch("core.llm_backend.genai", fake_genai), patch("core.llm_backend.types", fake_types), patch(
            "core.llm_backend.genai_errors", fake_errors
        ), patch("core.llm_backend.load_secure_api_key_into_environment", return_value=False), patch.dict(
            "os.environ",
            {"GOOGLE_API_KEY": "key1,key2", "GEMINI_MODEL": "gemini-2.5-flash", "GEMINI_BACKEND": "api"},
            clear=True,
        ):
            result = generate_text("prompt body", system_instruction="system note", temperature=0.2)

        self.assertEqual(result, "success text")
        self.assertEqual([entry[0] for entry in call_log], ["key1", "key2"])
        self.assertEqual(call_log[0][1], "gemini-2.5-flash")
        self.assertEqual(call_log[0][2], "prompt body")
        self.assertEqual(call_log[0][3], 0.2)
        self.assertEqual(call_log[0][4], "system note")

    def test_generate_text_does_not_retry_non_retryable_error(self):
        call_keys: list[str] = []

        def client_factory(api_key: str):
            def generate_content(*, model, contents, config):
                call_keys.append(api_key)
                raise ValueError("bad prompt")

            return FakeClient(api_key, generate_content)

        fake_types = SimpleNamespace(GenerateContentConfig=FakeConfig)
        fake_genai = FakeGenAI(client_factory)

        with patch("core.llm_backend.genai", fake_genai), patch("core.llm_backend.types", fake_types), patch(
            "core.llm_backend.load_secure_api_key_into_environment", return_value=False
        ), patch.dict(
            "os.environ",
            {"GOOGLE_API_KEY": "key1,key2", "GEMINI_MODEL": "gemini-2.5-flash", "GEMINI_BACKEND": "api"},
            clear=True,
        ):
            with self.assertRaises(LLMError):
                generate_text("prompt body")

        self.assertEqual(call_keys, ["key1"])


if __name__ == "__main__":
    unittest.main()
