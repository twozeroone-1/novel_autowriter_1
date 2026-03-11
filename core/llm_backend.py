import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from typing import Protocol

from core.api_key_store import load_secure_api_key_into_environment

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv(*args, **kwargs):
        return False

try:
    from google import genai
    from google.genai import errors as genai_errors
    from google.genai import types
except ModuleNotFoundError:
    genai = None
    genai_errors = None
    types = None

try:
    import httpx
except ModuleNotFoundError:
    httpx = None

load_dotenv(override=True)

VALID_BACKEND_MODES = {"auto", "api", "cli"}


class ApiBackendError(RuntimeError):
    """Raised when the Gemini API backend cannot produce usable text."""


class CliUnavailableError(RuntimeError):
    """Raised when Gemini CLI is not installed or cannot be found."""


class CliAuthError(RuntimeError):
    """Raised when Gemini CLI exists but is not authenticated."""


class CliInvocationError(RuntimeError):
    """Raised when Gemini CLI execution fails for non-auth reasons."""


CLI_FALLBACK_EXCEPTIONS = (CliUnavailableError, CliAuthError, CliInvocationError)


@dataclass(frozen=True)
class LlmRequest:
    prompt: str
    system_instruction: str | None
    temperature: float
    model_name: str


@dataclass(frozen=True)
class LlmBackendResult:
    text: str
    backend_used: str
    diagnostics: tuple[str, ...] = ()
    stderr_text: str = ""


@dataclass(frozen=True)
class GeminiCliStatus:
    available: bool
    path: str | None
    version: str | None = None
    authenticated: bool | None = None
    message: str = ""


class LlmBackend(Protocol):
    def generate(self, request: LlmRequest) -> LlmBackendResult: ...


def resolve_backend_mode(raw: str | None) -> str:
    value = (raw or "auto").strip().lower()
    return value if value in VALID_BACKEND_MODES else "auto"


def get_backend_gate_error(
    mode: str,
    *,
    has_api_key: bool,
    cli_status: GeminiCliStatus | None = None,
) -> str | None:
    resolved_mode = resolve_backend_mode(mode)
    cli_ready = bool(cli_status and cli_status.available and cli_status.authenticated is not False)
    cli_needs_auth = bool(cli_status and cli_status.available and cli_status.authenticated is False)

    if resolved_mode == "api":
        if has_api_key:
            return None
        return "API 키가 설정되지 않았습니다. 사이드바에서 먼저 설정해 주세요."

    if resolved_mode == "cli":
        if cli_ready:
            return None
        if cli_needs_auth:
            return "Gemini CLI OAuth 로그인이 필요합니다. 사이드바에서 CLI 연결 테스트로 상태를 확인해 주세요."
        return "Gemini CLI를 사용할 수 없습니다. 설치 상태와 OAuth 로그인을 확인해 주세요."

    if has_api_key or cli_ready:
        return None
    if cli_needs_auth:
        return "API 키가 없고 Gemini CLI OAuth 로그인도 완료되지 않았습니다. 사이드바에서 둘 중 하나를 먼저 준비해 주세요."
    return "API 키가 없고 Gemini CLI도 사용할 수 없습니다. 사이드바에서 API 키를 설정하거나 Gemini CLI를 준비해 주세요."


def find_gemini_cli_executable(platform_name: str | None = None) -> str | None:
    current_platform = platform_name or sys.platform
    candidates = ["gemini.cmd", "gemini"] if current_platform.startswith("win") else ["gemini"]
    for candidate in candidates:
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    return None


def compose_cli_prompt(prompt: str, system_instruction: str | None = None) -> str:
    if not system_instruction:
        return prompt
    return f"System instruction: {system_instruction}\n\nUser request: {prompt}"


def _should_retry_on_error(exc: Exception) -> bool:
    if genai_errors is not None and isinstance(exc, genai_errors.APIError):
        if isinstance(exc, genai_errors.ServerError):
            return True

        retryable_codes = {408, 429, 500, 502, 503, 504}
        retryable_statuses = {
            "DEADLINE_EXCEEDED",
            "RESOURCE_EXHAUSTED",
            "UNAVAILABLE",
        }
        error_code = getattr(exc, "code", None)
        error_status = str(getattr(exc, "status", "") or "").upper()
        return error_code in retryable_codes or error_status in retryable_statuses

    if httpx is not None and isinstance(exc, (httpx.TimeoutException, httpx.TransportError)):
        return True

    message = str(exc).lower()
    retryable_markers = (
        "connection reset",
        "deadline exceeded",
        "quota",
        "rate limit",
        "resource exhausted",
        "service unavailable",
        "temporarily unavailable",
        "timeout",
        "timed out",
        "unavailable",
    )

    fallback_type_names = {
        "DeadlineExceeded",
        "GoogleAPICallError",
        "ResourceExhausted",
        "RetryError",
        "ServiceUnavailable",
        "TooManyRequests",
        "TransportError",
    }
    type_name = exc.__class__.__name__
    module_name = exc.__class__.__module__.lower()
    if type_name not in fallback_type_names and not module_name.startswith(("google.", "httpx", "httpcore")):
        return False

    return any(marker in message for marker in retryable_markers)


def _detect_cli_auth_issue(output: str) -> bool:
    lowered = output.lower()
    auth_markers = (
        "login",
        "log in",
        "sign in",
        "authenticate",
        "oauth",
        "credential",
        "not authenticated",
        "no stored credentials",
    )
    return any(marker in lowered for marker in auth_markers)


def _build_cli_command(executable_path: str, model_name: str) -> list[str]:
    # Force the CLI into headless mode so chapter generation behaves like a
    # one-shot text request instead of dropping into interactive agent mode.
    command = [executable_path, "--output-format", "text", "--prompt", ""]
    if model_name.strip():
        command.extend(["--model", model_name.strip()])
    return command


def probe_gemini_cli(executable_path: str | None = None, timeout_seconds: int = 10) -> GeminiCliStatus:
    resolved_path = executable_path or find_gemini_cli_executable()
    if not resolved_path:
        return GeminiCliStatus(
            available=False,
            path=None,
            version=None,
            authenticated=None,
            message="Gemini CLI executable was not found.",
        )

    try:
        completed = subprocess.run(
            [resolved_path, "--version"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
        )
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired) as exc:
        return GeminiCliStatus(
            available=False,
            path=resolved_path,
            version=None,
            authenticated=None,
            message=f"Failed to read Gemini CLI version: {exc}",
        )

    version = (completed.stdout or "").strip() or None
    if completed.returncode != 0:
        message = (completed.stderr or completed.stdout or "").strip() or "Failed to read Gemini CLI version."
        return GeminiCliStatus(
            available=False,
            path=resolved_path,
            version=version,
            authenticated=None,
            message=message,
        )

    return GeminiCliStatus(
        available=True,
        path=resolved_path,
        version=version,
        authenticated=None,
        message="Gemini CLI is installed.",
    )


def test_gemini_cli_connection(
    model_name: str,
    executable_path: str | None = None,
    timeout_seconds: int = 30,
) -> GeminiCliStatus:
    status = probe_gemini_cli(executable_path=executable_path, timeout_seconds=min(timeout_seconds, 10))
    if not status.available:
        return status

    backend = GeminiCliBackend(executable_path=status.path, timeout_seconds=timeout_seconds)
    request = LlmRequest(
        prompt="Reply with OK only.",
        system_instruction=None,
        temperature=0.0,
        model_name=model_name,
    )
    try:
        backend.generate(request)
    except CliAuthError as exc:
        return GeminiCliStatus(
            available=True,
            path=status.path,
            version=status.version,
            authenticated=False,
            message=str(exc),
        )
    except CLI_FALLBACK_EXCEPTIONS as exc:
        return GeminiCliStatus(
            available=True,
            path=status.path,
            version=status.version,
            authenticated=None,
            message=str(exc),
        )

    return GeminiCliStatus(
        available=True,
        path=status.path,
        version=status.version,
        authenticated=True,
        message="Gemini CLI connection test succeeded.",
    )


class GeminiCliBackend:
    def __init__(self, executable_path: str | None = None, timeout_seconds: int = 180):
        self.executable_path = executable_path or find_gemini_cli_executable()
        self.timeout_seconds = timeout_seconds

    def generate(self, request: LlmRequest) -> LlmBackendResult:
        if not self.executable_path:
            raise CliUnavailableError("Gemini CLI executable was not found.")

        prompt_text = compose_cli_prompt(request.prompt, request.system_instruction)
        command = _build_cli_command(self.executable_path, request.model_name)

        try:
            with tempfile.TemporaryDirectory(prefix="novel-autowriter-gemini-cli-") as workdir:
                completed = subprocess.run(
                    command,
                    input=prompt_text,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=self.timeout_seconds,
                    cwd=workdir,
                )
        except FileNotFoundError as exc:
            raise CliUnavailableError("Gemini CLI executable was not found.") from exc
        except subprocess.TimeoutExpired as exc:
            raise CliInvocationError("Gemini CLI did not finish within the timeout.") from exc
        except OSError as exc:
            raise CliInvocationError(f"Gemini CLI invocation failed: {exc}") from exc

        output = (completed.stdout or "").strip()
        error_output = (completed.stderr or "").strip()
        combined_output = "\n".join(part for part in (output, error_output) if part).strip()

        if completed.returncode != 0:
            if _detect_cli_auth_issue(combined_output):
                raise CliAuthError(combined_output or "Gemini CLI authentication is required.")
            raise CliInvocationError(combined_output or f"Gemini CLI exited with code {completed.returncode}.")

        if not output:
            if _detect_cli_auth_issue(combined_output):
                raise CliAuthError(combined_output or "Gemini CLI authentication is required.")
            raise CliInvocationError("Gemini CLI returned an empty response.")

        return LlmBackendResult(text=output, backend_used="cli", diagnostics=(), stderr_text=error_output)


class GeminiApiBackend:
    def generate(self, request: LlmRequest) -> LlmBackendResult:
        if genai is None or types is None:
            raise ApiBackendError(
                "google-genai is not installed. Run `pip install -r requirements.txt` and try again."
            )

        config = types.GenerateContentConfig(temperature=request.temperature)
        if request.system_instruction:
            config.system_instruction = request.system_instruction

        load_secure_api_key_into_environment()
        api_key_env = os.getenv("GOOGLE_API_KEY", "")
        if not api_key_env.strip():
            raise ApiBackendError("GOOGLE_API_KEY is not configured.")

        api_keys = [key.strip() for key in api_key_env.split(",") if key.strip()]
        if not api_keys:
            raise ApiBackendError("No valid GOOGLE_API_KEY values were found.")

        last_error: Exception | None = None
        for index, api_key in enumerate(api_keys):
            try:
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model=request.model_name,
                    contents=request.prompt,
                    config=config,
                )
                text = getattr(response, "text", None)
                if not text or not text.strip():
                    raise ApiBackendError("Gemini API returned an empty response.")
                return LlmBackendResult(text=text, backend_used="api", diagnostics=(), stderr_text="")
            except MemoryError:
                raise
            except ApiBackendError:
                raise
            except Exception as exc:
                if not _should_retry_on_error(exc):
                    raise ApiBackendError(
                        f"Gemini API call failed for model {request.model_name}: {exc}"
                    ) from exc
                print(f"[Fallback] API Key {index + 1}/{len(api_keys)} failed: {exc}")
                last_error = exc

        raise ApiBackendError(
            f"Gemini API call failed for model {request.model_name}. Last error: {last_error}"
        )


def generate_via_backend_mode(
    mode: str,
    request: LlmRequest,
    *,
    cli_backend: LlmBackend | None = None,
    api_backend: LlmBackend | None = None,
) -> LlmBackendResult:
    resolved_mode = resolve_backend_mode(mode)
    cli_backend = cli_backend or GeminiCliBackend()
    api_backend = api_backend or GeminiApiBackend()

    if resolved_mode == "api":
        return api_backend.generate(request)

    if resolved_mode == "cli":
        return cli_backend.generate(request)

    diagnostics: list[str] = []
    try:
        return cli_backend.generate(request)
    except CLI_FALLBACK_EXCEPTIONS as exc:
        diagnostics.append(str(exc))

    api_result = api_backend.generate(request)
    if diagnostics:
        return LlmBackendResult(
            text=api_result.text,
            backend_used=api_result.backend_used,
            diagnostics=tuple(diagnostics),
        )
    return api_result
