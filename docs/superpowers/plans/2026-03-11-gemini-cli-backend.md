# Gemini CLI Backend Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `Gemini API`와 `Gemini CLI OAuth`를 함께 지원하고, 앱 전체 기본값 `auto`에서 CLI 우선 후 API 폴백이 동작하도록 만든다.

**Architecture:** 기존 [core/llm.py](/c:/Users/W/novel_autowriter_1/core/llm.py)를 파사드로 유지하고, 실제 호출은 새 백엔드 계층에서 처리한다. UI는 사이드바에 앱 전체 기본 백엔드 설정과 CLI 상태 패널을 추가하고, `Generator`, `Reviewer`, `Planner`는 그대로 공통 LLM 진입점을 사용한다.

**Tech Stack:** Python, Streamlit, subprocess, google-genai, unittest, dotenv

---

## File Structure

### New files

- `docs/superpowers/specs/2026-03-11-gemini-cli-backend-design.md`
  - 설계 문서
- `docs/superpowers/plans/2026-03-11-gemini-cli-backend.md`
  - 구현 계획 문서
- `core/llm_backend.py`
  - 백엔드 모드, CLI/API adapter, backend resolver
- `tests/test_llm_backends.py`
  - backend resolver, CLI command builder, fallback 정책 테스트
- `tests/test_cli_status.py`
  - CLI 상태 프로브와 UI 보조 헬퍼 테스트

### Modified files

- `core/llm.py`
  - 파사드 유지, 내부 백엔드 호출로 전환
- `core/generator.py`
  - `generate_text()` 호출이 새 백엔드 계약과 호환되는지 확인
- `core/reviewer.py`
  - 동일
- `core/planner.py`
  - 동일
- `ui/workspace.py`
  - 사이드바에 백엔드 선택, CLI 상태, 테스트 버튼 추가
- `ui/app.py`
  - 앱 전체 설정 로딩/환경 키 반영
- `requirements.txt`
  - 필요 시 추가 의존성 반영
- `tests/test_llm_retry.py`
  - API fallback 관련 기존 테스트를 새 resolver 기준으로 조정

---

## Chunk 1: Backend Abstraction

### Task 1: Add failing tests for backend mode resolution

**Files:**
- Create: `tests/test_llm_backends.py`
- Modify: none
- Test: `tests/test_llm_backends.py`

- [ ] **Step 1: Write the failing test**

```python
def test_resolve_backend_mode_uses_auto_as_default():
    assert resolve_backend_mode(None) == "auto"


def test_resolve_backend_mode_accepts_api_and_cli():
    assert resolve_backend_mode("api") == "api"
    assert resolve_backend_mode("cli") == "cli"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `venv\Scripts\python.exe -m unittest tests.test_llm_backends -v`
Expected: FAIL because `core.llm_backend` does not exist yet

- [ ] **Step 3: Write minimal implementation**

Create `core/llm_backend.py` with:

```python
VALID_BACKEND_MODES = {"auto", "api", "cli"}


def resolve_backend_mode(raw: str | None) -> str:
    value = (raw or "auto").strip().lower()
    return value if value in VALID_BACKEND_MODES else "auto"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `venv\Scripts\python.exe -m unittest tests.test_llm_backends -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/llm_backend.py tests/test_llm_backends.py
git commit -m "Add LLM backend mode resolver"
```

### Task 2: Add failing tests for Gemini CLI executable resolution

**Files:**
- Modify: `tests/test_llm_backends.py`
- Modify: `core/llm_backend.py`
- Test: `tests/test_llm_backends.py`

- [ ] **Step 1: Write the failing test**

```python
@patch("shutil.which")
def test_find_gemini_cli_executable_prefers_cmd_on_windows(mock_which):
    mock_which.side_effect = lambda name: {
        "gemini.cmd": r"C:\\Users\\W\\AppData\\Roaming\\npm\\gemini.cmd",
        "gemini": None,
    }.get(name)
    self.assertEqual(
        find_gemini_cli_executable("win32"),
        r"C:\\Users\\W\\AppData\\Roaming\\npm\\gemini.cmd",
    )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `venv\Scripts\python.exe -m unittest tests.test_llm_backends -v`
Expected: FAIL because `find_gemini_cli_executable` is missing

- [ ] **Step 3: Write minimal implementation**

Add:

```python
def find_gemini_cli_executable(platform_name: str | None = None) -> str | None:
    names = ["gemini.cmd", "gemini"] if (platform_name or sys.platform).startswith("win") else ["gemini"]
    for name in names:
        path = shutil.which(name)
        if path:
            return path
    return None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `venv\Scripts\python.exe -m unittest tests.test_llm_backends -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/llm_backend.py tests/test_llm_backends.py
git commit -m "Detect Gemini CLI executable path"
```

### Task 3: Add failing tests for CLI prompt composition

**Files:**
- Modify: `tests/test_llm_backends.py`
- Modify: `core/llm_backend.py`
- Test: `tests/test_llm_backends.py`

- [ ] **Step 1: Write the failing test**

```python
def test_compose_cli_prompt_includes_system_instruction_block():
    prompt = compose_cli_prompt("user body", system_instruction="system note")
    assert "[SYSTEM INSTRUCTION]" in prompt
    assert "system note" in prompt
    assert "[USER PROMPT]" in prompt
    assert "user body" in prompt
```

- [ ] **Step 2: Run test to verify it fails**

Run: `venv\Scripts\python.exe -m unittest tests.test_llm_backends -v`
Expected: FAIL because `compose_cli_prompt` is missing

- [ ] **Step 3: Write minimal implementation**

Add:

```python
def compose_cli_prompt(prompt: str, system_instruction: str | None = None) -> str:
    if not system_instruction:
        return prompt
    return f"[SYSTEM INSTRUCTION]\\n{system_instruction}\\n\\n[USER PROMPT]\\n{prompt}"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `venv\Scripts\python.exe -m unittest tests.test_llm_backends -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/llm_backend.py tests/test_llm_backends.py
git commit -m "Compose Gemini CLI prompt with system block"
```

## Chunk 2: CLI Invocation and Auto Fallback

### Task 4: Add failing tests for CLI invocation wrapper

**Files:**
- Modify: `tests/test_llm_backends.py`
- Modify: `core/llm_backend.py`
- Test: `tests/test_llm_backends.py`

- [ ] **Step 1: Write the failing test**

```python
@patch("subprocess.run")
def test_gemini_cli_backend_returns_stdout_text(mock_run):
    mock_run.return_value = subprocess.CompletedProcess(
        args=["gemini.cmd"],
        returncode=0,
        stdout="generated text",
        stderr="",
    )
    backend = GeminiCliBackend(executable_path="gemini.cmd")
    result = backend.generate(LlmRequest(prompt="hello", system_instruction=None, temperature=0.7, model_name="gemini-2.5-flash"))
    self.assertEqual(result.text, "generated text")
    self.assertEqual(result.backend_used, "cli")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `venv\Scripts\python.exe -m unittest tests.test_llm_backends -v`
Expected: FAIL because `GeminiCliBackend` and request/result types are missing

- [ ] **Step 3: Write minimal implementation**

Add dataclasses and minimal subprocess wrapper in `core/llm_backend.py`.

- [ ] **Step 4: Run test to verify it passes**

Run: `venv\Scripts\python.exe -m unittest tests.test_llm_backends -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/llm_backend.py tests/test_llm_backends.py
git commit -m "Add Gemini CLI backend wrapper"
```

### Task 5: Add failing tests for auto fallback from CLI to API

**Files:**
- Modify: `tests/test_llm_backends.py`
- Modify: `core/llm_backend.py`
- Test: `tests/test_llm_backends.py`

- [ ] **Step 1: Write the failing test**

```python
def test_auto_backend_falls_back_to_api_when_cli_unavailable():
    cli_backend = FakeCliBackend(error=CliUnavailableError("missing"))
    api_backend = FakeApiBackend(text="api text")
    result = generate_via_backend_mode("auto", request, cli_backend=cli_backend, api_backend=api_backend)
    assert result.text == "api text"
    assert result.backend_used == "api"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `venv\Scripts\python.exe -m unittest tests.test_llm_backends -v`
Expected: FAIL because resolver is missing

- [ ] **Step 3: Write minimal implementation**

Add `generate_via_backend_mode()` with:

- `auto`: try CLI, then API on CLI availability/auth/invocation failure
- `cli`: CLI only
- `api`: API only

- [ ] **Step 4: Run test to verify it passes**

Run: `venv\Scripts\python.exe -m unittest tests.test_llm_backends -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/llm_backend.py tests/test_llm_backends.py
git commit -m "Add auto fallback between Gemini CLI and API"
```

### Task 6: Add failing tests for forced CLI error propagation

**Files:**
- Modify: `tests/test_llm_backends.py`
- Modify: `core/llm_backend.py`
- Test: `tests/test_llm_backends.py`

- [ ] **Step 1: Write the failing test**

```python
def test_cli_mode_does_not_fallback_to_api():
    cli_backend = FakeCliBackend(error=CliAuthError("not logged in"))
    api_backend = FakeApiBackend(text="api text")
    with self.assertRaises(CliAuthError):
        generate_via_backend_mode("cli", request, cli_backend=cli_backend, api_backend=api_backend)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `venv\Scripts\python.exe -m unittest tests.test_llm_backends -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

Adjust resolver so `cli` mode never falls back.

- [ ] **Step 4: Run test to verify it passes**

Run: `venv\Scripts\python.exe -m unittest tests.test_llm_backends -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/llm_backend.py tests/test_llm_backends.py
git commit -m "Preserve forced CLI mode failures"
```

## Chunk 3: Integrate Backends into Existing LLM Facade

### Task 7: Add failing tests for `core.llm.generate_text()` backend selection

**Files:**
- Modify: `tests/test_llm_retry.py`
- Modify: `core/llm.py`
- Test: `tests/test_llm_retry.py`

- [ ] **Step 1: Write the failing test**

```python
@patch("core.llm.generate_via_backend_mode")
def test_generate_text_reads_backend_mode_from_environment(mock_generate):
    mock_generate.return_value = LlmBackendResult(text="hello", backend_used="cli", diagnostics=[])
    with patch.dict("os.environ", {"GEMINI_BACKEND": "auto", "GEMINI_MODEL": "gemini-2.5-flash"}, clear=True):
        result = generate_text("prompt body", system_instruction="sys")
    self.assertEqual(result, "hello")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `venv\Scripts\python.exe -m unittest tests.test_llm_retry -v`
Expected: FAIL because `core.llm` still bypasses backend resolver

- [ ] **Step 3: Write minimal implementation**

Modify `core/llm.py` so:

- it still exposes `generate_text()`
- it builds `LlmRequest`
- it reads `GEMINI_BACKEND`
- it delegates to `generate_via_backend_mode()`

- [ ] **Step 4: Run test to verify it passes**

Run: `venv\Scripts\python.exe -m unittest tests.test_llm_retry -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/llm.py tests/test_llm_retry.py
git commit -m "Route generate_text through backend resolver"
```

### Task 8: Verify generator/reviewer/planner compatibility without code churn

**Files:**
- Modify: `tests/test_automator.py`
- Modify: `tests/test_reviewer.py`
- Modify: `tests/test_llm_parser.py`
- Modify: `core/generator.py`
- Modify: `core/reviewer.py`
- Modify: `core/planner.py`
- Test: `tests/test_automator.py`, `tests/test_reviewer.py`, `tests/test_llm_parser.py`

- [ ] **Step 1: Write the failing tests**

Add regression coverage that:

- `Generator.create_chapter()` still returns plain text from common facade
- `Reviewer.review_chapter()` and `revise_draft()` still call common facade
- JSON extraction helpers still work on CLI-like plain text output

- [ ] **Step 2: Run tests to verify they fail only where expected**

Run:

```bash
venv\Scripts\python.exe -m unittest tests.test_automator tests.test_reviewer tests.test_llm_parser -v
```

Expected: FAIL only on changed assumptions

- [ ] **Step 3: Write minimal implementation**

Only touch app code if any caller needs adaptation to the new facade contract. Prefer no production code change if tests pass once `core.llm` is updated.

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
venv\Scripts\python.exe -m unittest tests.test_automator tests.test_reviewer tests.test_llm_parser -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/generator.py core/reviewer.py core/planner.py tests/test_automator.py tests/test_reviewer.py tests/test_llm_parser.py
git commit -m "Keep generation and review flows compatible with backend abstraction"
```

## Chunk 4: Sidebar UX for Backend Selection and CLI Status

### Task 9: Add failing tests for backend settings helpers

**Files:**
- Create: `tests/test_cli_status.py`
- Modify: `ui/workspace.py`
- Test: `tests/test_cli_status.py`

- [ ] **Step 1: Write the failing test**

```python
def test_format_cli_status_reports_installed_but_untested():
    status = format_cli_status({"available": True, "authenticated": None, "path": "gemini.cmd"})
    self.assertIn("설치됨", status)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `venv\Scripts\python.exe -m unittest tests.test_cli_status -v`
Expected: FAIL because helper is missing

- [ ] **Step 3: Write minimal implementation**

Add pure helpers in `ui/workspace.py` or a small new helper module:

- `format_cli_status()`
- `get_backend_mode_options()`

- [ ] **Step 4: Run test to verify it passes**

Run: `venv\Scripts\python.exe -m unittest tests.test_cli_status -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add ui/workspace.py tests/test_cli_status.py
git commit -m "Add Gemini CLI status helpers"
```

### Task 10: Add sidebar controls for backend mode and CLI test

**Files:**
- Modify: `ui/workspace.py`
- Modify: `ui/app.py`
- Test: `tests/test_cli_status.py`, `tests/test_ui_helpers.py`

- [ ] **Step 1: Write the failing tests**

Add tests for:

- backend mode normalization from `.env`
- CLI status strings for installed/missing/auth-failed

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
venv\Scripts\python.exe -m unittest tests.test_cli_status tests.test_ui_helpers -v
```

Expected: FAIL on new helper expectations

- [ ] **Step 3: Write minimal implementation**

In sidebar:

- add `selectbox` for `LLM 백엔드`
- store to `.env` as `GEMINI_BACKEND`
- show detected executable path
- add `CLI 연결 테스트` button
- surface concise status messages

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
venv\Scripts\python.exe -m unittest tests.test_cli_status tests.test_ui_helpers -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add ui/workspace.py ui/app.py tests/test_cli_status.py tests/test_ui_helpers.py
git commit -m "Add backend selector and Gemini CLI status UI"
```

## Chunk 5: End-to-End Verification

### Task 11: Verify full suite stays green

**Files:**
- Modify: none unless failures reveal required fixes
- Test: full suite

- [ ] **Step 1: Run full test suite**

Run:

```bash
venv\Scripts\python.exe -m unittest discover -s tests -v
```

Expected: PASS with zero failures

- [ ] **Step 2: Run syntax verification**

Run:

```bash
venv\Scripts\python.exe -m py_compile core\llm.py core\llm_backend.py ui\workspace.py ui\app.py core\generator.py core\reviewer.py core\planner.py
```

Expected: no output

- [ ] **Step 3: Run import smoke test**

Run:

```bash
@"
import main
print('import ok')
"@ | venv\Scripts\python.exe -
```

Expected: `import ok`

- [ ] **Step 4: Manual smoke checks**

Check these flows manually in Streamlit:

- `api` mode + API key only
- `cli` mode + OAuth-authenticated Gemini CLI
- `auto` mode + CLI available
- `auto` mode + CLI unavailable + API fallback
- `[2] 회차 생성`
- `[3] 원고 검수`
- `[5] 아이디어/제목`
- `[6] 대형 플롯`

- [ ] **Step 5: Commit**

```bash
git add .
git commit -m "Add Gemini CLI backend support with auto fallback"
```

## Notes for the Implementer

- Do not inspect or parse Gemini CLI OAuth token files directly.
- Invoke the official CLI process only.
- On Windows, always prefer `gemini.cmd` over `gemini.ps1`.
- Keep backend selection app-global in v1. Do not add per-feature overrides unless a failing requirement emerges.
- Keep CLI integration text-only in v1. Do not depend on undocumented JSON event schemas unless text mode proves insufficient.
