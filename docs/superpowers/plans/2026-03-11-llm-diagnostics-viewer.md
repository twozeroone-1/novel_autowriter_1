# LLM Diagnostics Viewer Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a diagnostics-only viewer that records recent LLM requests and exposes a hidden 24-hour troubleshooting view without cluttering the main writing workflow.

**Architecture:** Keep storage and retention logic in a new `core/diagnostics.py` module, keep display helpers in a new `ui/diagnostics.py` module, and thread structured logging through the existing `core.llm.generate_text()` facade. UI integration stays limited to the sidebar summary and a collapsed advanced section inside tab `[1]`.

**Tech Stack:** Python, Streamlit, JSONL, pathlib, unittest

---

## File Structure

### New files

- `docs/superpowers/plans/2026-03-11-llm-diagnostics-viewer.md`
  - implementation plan for the approved design
- `core/diagnostics.py`
  - record schema, append/load helpers, retention cleanup, summary helpers
- `ui/diagnostics.py`
  - pure helpers and rendering functions for sidebar summary and detailed viewer
- `tests/test_diagnostics.py`
  - storage, retention, parsing, and summary coverage
- `tests/test_diagnostics_ui.py`
  - filter and summary helper coverage for the UI layer

### Modified files

- `core/llm_backend.py`
  - expose structured backend diagnostics needed for logging, especially CLI stderr and fallback reasons
- `core/llm.py`
  - log both success and failure through the shared diagnostics path
- `core/generator.py`
  - pass feature and project context into `generate_text()`
- `core/reviewer.py`
  - pass feature and project context into `generate_text()`
- `core/planner.py`
  - pass feature and project context into `generate_text()`
- `ui/workspace.py`
  - add sidebar summary and advanced diagnostics section wiring
- `tests/test_llm_retry.py`
  - verify structured logging behavior around the `core.llm` facade
- `tests/test_reviewer.py`
  - keep review flows compatible after `generate_text()` signature expansion
- `tests/test_llm_parser.py`
  - keep generator JSON extraction stable after caller updates

---

## Chunk 1: Diagnostics Storage Layer

### Task 1: Add failing tests for JSONL storage and retention

**Files:**
- Create: `tests/test_diagnostics.py`
- Modify: none
- Test: `tests/test_diagnostics.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_append_and_read_recent_runs_newest_first(self):
    append_llm_run(self.project_name, build_record(timestamp=self.now - timedelta(minutes=5)))
    append_llm_run(self.project_name, build_record(timestamp=self.now))

    records = load_recent_llm_runs(self.project_name, now=self.now)

    self.assertEqual(len(records), 2)
    self.assertGreater(records[0]["timestamp"], records[1]["timestamp"])


def test_cleanup_drops_records_older_than_24_hours(self):
    append_llm_run(self.project_name, build_record(timestamp=self.now - timedelta(hours=25)))
    append_llm_run(self.project_name, build_record(timestamp=self.now - timedelta(hours=1)))

    records = load_recent_llm_runs(self.project_name, now=self.now)

    self.assertEqual(len(records), 1)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `venv\Scripts\python.exe -m unittest tests.test_diagnostics -v`

Expected: FAIL because `core.diagnostics` does not exist yet

- [ ] **Step 3: Write minimal implementation**

Create `core/diagnostics.py` with:

```python
def get_diagnostics_dir(project_name: str) -> Path:
    return DATA_PROJECTS_DIR / project_name / "diagnostics" / "llm_runs"


def append_llm_run(project_name: str, record: dict) -> None:
    target_dir = get_diagnostics_dir(project_name)
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / f"{record['timestamp'][:10]}.jsonl"
    with target_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `venv\Scripts\python.exe -m unittest tests.test_diagnostics -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/diagnostics.py tests/test_diagnostics.py
git commit -m "Add LLM diagnostics storage helpers"
```

### Task 2: Add failing tests for malformed lines and summary helpers

**Files:**
- Modify: `tests/test_diagnostics.py`
- Modify: `core/diagnostics.py`
- Test: `tests/test_diagnostics.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_load_recent_runs_skips_malformed_jsonl_lines(self):
    log_path.write_text('{"ok": 1}\nnot-json\n', encoding="utf-8")
    records = load_recent_llm_runs(self.project_name, now=self.now)
    self.assertEqual(len(records), 1)


def test_build_recent_summary_counts_failures_and_latest_backend(self):
    records = [
        {"success": True, "actual_backend": "cli"},
        {"success": False, "actual_backend": "api"},
    ]
    summary = build_recent_summary(records)
    self.assertEqual(summary["run_count"], 2)
    self.assertEqual(summary["failure_count"], 1)
    self.assertEqual(summary["latest_backend"], "cli")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `venv\Scripts\python.exe -m unittest tests.test_diagnostics -v`

Expected: FAIL because malformed-line handling and summary helpers are missing

- [ ] **Step 3: Write minimal implementation**

Add to `core/diagnostics.py`:

```python
def load_recent_llm_runs(project_name: str, *, now: datetime | None = None) -> list[dict]:
    ...
    try:
        record = json.loads(line)
    except json.JSONDecodeError:
        continue


def build_recent_summary(records: list[dict]) -> dict:
    return {
        "run_count": len(records),
        "failure_count": sum(1 for record in records if not record.get("success")),
        "latest_backend": records[0].get("actual_backend") if records else None,
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `venv\Scripts\python.exe -m unittest tests.test_diagnostics -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/diagnostics.py tests/test_diagnostics.py
git commit -m "Handle malformed diagnostics logs and summaries"
```

---

## Chunk 2: Thread Structured Logging Through the LLM Facade

### Task 3: Add failing tests for `generate_text()` success logging

**Files:**
- Modify: `tests/test_llm_retry.py`
- Modify: `core/llm.py`
- Test: `tests/test_llm_retry.py`

- [ ] **Step 1: Write the failing test**

```python
@patch("core.llm.append_llm_run")
@patch("core.llm.generate_via_backend_mode")
def test_generate_text_logs_success_with_backend_metadata(mock_generate, mock_append):
    mock_generate.return_value = LlmBackendResult(
        text="ok",
        backend_used="cli",
        diagnostics=("cli primary path",),
    )

    result = generate_text(
        "prompt body",
        system_instruction="system note",
        project_name="proj",
        feature="idea",
    )

    self.assertEqual(result, "ok")
    mock_append.assert_called_once()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `venv\Scripts\python.exe -m unittest tests.test_llm_retry -v`

Expected: FAIL because `generate_text()` does not yet accept `project_name` and `feature`

- [ ] **Step 3: Write minimal implementation**

Update `core/llm.py` so `generate_text()` accepts:

```python
def generate_text(
    prompt: str,
    system_instruction: str | None = None,
    temperature: float = 0.7,
    *,
    project_name: str | None = None,
    feature: str = "generic",
) -> str:
```

and logs success records after `generate_via_backend_mode()`.

- [ ] **Step 4: Run test to verify it passes**

Run: `venv\Scripts\python.exe -m unittest tests.test_llm_retry -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/llm.py tests/test_llm_retry.py
git commit -m "Log successful LLM facade calls"
```

### Task 4: Add failing tests for failure logging and auto fallback notes

**Files:**
- Modify: `tests/test_llm_retry.py`
- Modify: `core/llm.py`
- Modify: `core/llm_backend.py`
- Test: `tests/test_llm_retry.py`

- [ ] **Step 1: Write the failing tests**

```python
@patch("core.llm.append_llm_run")
@patch("core.llm.generate_via_backend_mode")
def test_generate_text_logs_failure_before_raising_llm_error(mock_generate, mock_append):
    mock_generate.side_effect = ApiBackendError("api failed")

    with self.assertRaises(LLMError):
        generate_text("prompt", project_name="proj", feature="review")

    mock_append.assert_called_once()


def test_auto_mode_preserves_cli_failure_reason_in_result():
    result = generate_via_backend_mode("auto", request, cli_backend=failing_cli, api_backend=working_api)
    self.assertEqual(result.backend_used, "api")
    self.assertIn("cli", " ".join(result.diagnostics).lower())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `venv\Scripts\python.exe -m unittest tests.test_llm_retry -v`

Expected: FAIL because failure logging and structured fallback details are incomplete

- [ ] **Step 3: Write minimal implementation**

Adjust `core/llm_backend.py` and `core/llm.py` so:

- `LlmBackendResult` carries enough structured metadata for logging
- CLI success keeps `stderr_text`
- auto fallback preserves the CLI failure note in `diagnostics`
- failure paths log `error_text` before raising `LLMError`

Representative shape:

```python
@dataclass(frozen=True)
class LlmBackendResult:
    text: str
    backend_used: str
    diagnostics: tuple[str, ...] = ()
    stderr_text: str = ""
```

- [ ] **Step 4: Run test to verify it passes**

Run: `venv\Scripts\python.exe -m unittest tests.test_llm_retry -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/llm.py core/llm_backend.py tests/test_llm_retry.py
git commit -m "Log failed LLM calls and fallback details"
```

### Task 5: Update generator, reviewer, and planner call sites with feature labels

**Files:**
- Modify: `core/generator.py`
- Modify: `core/reviewer.py`
- Modify: `core/planner.py`
- Modify: `tests/test_reviewer.py`
- Modify: `tests/test_llm_parser.py`
- Test: `tests/test_reviewer.py`, `tests/test_llm_parser.py`

- [ ] **Step 1: Write the failing regression tests**

Add assertions that patched `generate_text()` receives the correct labels, for example:

```python
mock_generate.assert_called_with(
    ANY,
    system_instruction=ANY,
    project_name="sample_project",
    feature="review",
)
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
venv\Scripts\python.exe -m unittest tests.test_reviewer tests.test_llm_parser -v
```

Expected: FAIL on missing keyword arguments

- [ ] **Step 3: Write minimal implementation**

Map features like this:

- `Generator.create_chapter()` -> `chapter_generate`
- `Generator.summarize_chapter()` -> `chapter_summary`
- `Generator.compress_history_summary()` -> `history_compress`
- `Generator.elaborate_worldview()` -> `worldview_expand`
- `Generator.compress_worldview()` -> `worldview_compress`
- `Generator.structure_style_guide()` -> `style_structure`
- `Generator.structure_continuity()` -> `continuity_structure`
- `Generator.summarize_state()` -> `state_summary`
- `Generator.generate_tone()` -> `tone_suggest`
- `Generator.generate_characters()` -> `character_extract`
- `Reviewer.review_chapter()` -> `review`
- `Reviewer.revise_draft()` -> `revise`
- `Planner.suggest_ideas()` -> `idea`
- `Planner.build_macro_plot()` -> `plot`

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
venv\Scripts\python.exe -m unittest tests.test_reviewer tests.test_llm_parser -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/generator.py core/reviewer.py core/planner.py tests/test_reviewer.py tests/test_llm_parser.py
git commit -m "Label LLM calls with project and feature context"
```

---

## Chunk 3: Hidden Diagnostics UI

### Task 6: Add failing tests for UI summary and filter helpers

**Files:**
- Create: `tests/test_diagnostics_ui.py`
- Create: `ui/diagnostics.py`
- Test: `tests/test_diagnostics_ui.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_format_sidebar_summary_uses_compact_metadata_only(self):
    summary = format_sidebar_summary({"run_count": 3, "failure_count": 1, "latest_backend": "cli"})
    self.assertIn("3 runs", summary)
    self.assertIn("1 failed", summary)
    self.assertIn("cli", summary)


def test_filter_runs_by_success_backend_and_model(self):
    filtered = filter_runs(
        runs,
        success_filter="failed",
        requested_backend="auto",
        actual_backend="api",
        model_name="gemini-2.5-flash",
    )
    self.assertEqual(len(filtered), 1)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `venv\Scripts\python.exe -m unittest tests.test_diagnostics_ui -v`

Expected: FAIL because `ui.diagnostics` does not exist yet

- [ ] **Step 3: Write minimal implementation**

Create `ui/diagnostics.py` with pure helpers first:

```python
def format_sidebar_summary(summary: dict) -> str:
    return f"24h {summary['run_count']} runs / {summary['failure_count']} failed / last {summary['latest_backend'] or '-'}"


def filter_runs(...):
    ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `venv\Scripts\python.exe -m unittest tests.test_diagnostics_ui -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add ui/diagnostics.py tests/test_diagnostics_ui.py
git commit -m "Add diagnostics UI helper functions"
```

### Task 7: Wire sidebar summary into `ui/workspace.py`

**Files:**
- Modify: `ui/workspace.py`
- Modify: `tests/test_ui_helpers.py`
- Test: `tests/test_diagnostics_ui.py`, `tests/test_ui_helpers.py`

- [ ] **Step 1: Write the failing tests**

Add helper-level tests for:

- hidden diagnostics summary text when no records exist
- summary text when recent failures exist

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
venv\Scripts\python.exe -m unittest tests.test_diagnostics_ui tests.test_ui_helpers -v
```

Expected: FAIL on missing sidebar integration helpers

- [ ] **Step 3: Write minimal implementation**

In `ui/workspace.py`:

- load recent project diagnostics summary in `render_sidebar()`
- show only metadata near the backend status block
- add a cue like `Open the advanced diagnostics section in tab [1]` or a state flag button

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
venv\Scripts\python.exe -m unittest tests.test_diagnostics_ui tests.test_ui_helpers -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add ui/workspace.py tests/test_ui_helpers.py tests/test_diagnostics_ui.py
git commit -m "Show compact diagnostics summary in sidebar"
```

### Task 8: Add the advanced diagnostics viewer to tab `[1]`

**Files:**
- Modify: `ui/workspace.py`
- Modify: `ui/diagnostics.py`
- Modify: `tests/test_diagnostics_ui.py`
- Test: `tests/test_diagnostics_ui.py`

- [ ] **Step 1: Write the failing tests**

Add tests for pure rendering helpers that prepare:

- newest-first rows
- expanded raw details payloads
- warning text for sensitive content

- [ ] **Step 2: Run tests to verify they fail**

Run: `venv\Scripts\python.exe -m unittest tests.test_diagnostics_ui -v`

Expected: FAIL on missing detail-view helpers

- [ ] **Step 3: Write minimal implementation**

In `ui/diagnostics.py`, add functions like:

```python
def build_detail_rows(records: list[dict]) -> list[dict]:
    ...


def render_diagnostics_panel(project_name: str) -> None:
    ...
```

In `ui/workspace.py`, call `render_diagnostics_panel(generator.ctx.project_name)` at the bottom of `render_project_settings_tab()`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `venv\Scripts\python.exe -m unittest tests.test_diagnostics_ui -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add ui/workspace.py ui/diagnostics.py tests/test_diagnostics_ui.py
git commit -m "Add advanced LLM diagnostics viewer"
```

---

## Chunk 4: Verification

### Task 9: Run focused test suites

**Files:**
- Modify: none unless failures require fixes
- Test: focused diagnostics suites

- [ ] **Step 1: Run diagnostics storage tests**

Run: `venv\Scripts\python.exe -m unittest tests.test_diagnostics tests.test_diagnostics_ui -v`

Expected: PASS

- [ ] **Step 2: Run LLM facade regression tests**

Run: `venv\Scripts\python.exe -m unittest tests.test_llm_retry tests.test_reviewer tests.test_llm_parser -v`

Expected: PASS

- [ ] **Step 3: Run syntax verification**

Run:

```bash
venv\Scripts\python.exe -m py_compile core\diagnostics.py ui\diagnostics.py core\llm.py core\llm_backend.py core\generator.py core\reviewer.py core\planner.py ui\workspace.py
```

Expected: no output

- [ ] **Step 4: Commit any final fixups**

```bash
git add .
git commit -m "Finish LLM diagnostics viewer implementation"
```

### Task 10: Run full verification and manual smoke checks

**Files:**
- Modify: none unless failures reveal required fixes
- Test: full suite and manual UI flow

- [ ] **Step 1: Run the full test suite**

Run: `venv\Scripts\python.exe -m unittest discover -s tests -v`

Expected: PASS with zero failures

- [ ] **Step 2: Run import smoke test**

Run:

```bash
@"
import main
print('import ok')
"@ | venv\Scripts\python.exe -
```

Expected: `import ok`

- [ ] **Step 3: Manual Streamlit smoke checks**

Verify:

- idea generation creates a success record
- review failure creates a failure record
- `auto` mode fallback records `requested_backend=auto` and `actual_backend=api`
- sidebar shows only compact counts and backend summary
- tab `[1]` advanced section shows raw prompt and response only when expanded
- records older than 24 hours disappear automatically

- [ ] **Step 4: Final verification note**

Record the exact commands run and the final test count in the completion summary before claiming success.

## Notes for the Implementer

- Do not add a `[7]` top-level tab.
- Keep diagnostics failures non-fatal to the main writing flow.
- Do not render raw prompt or response text in the sidebar.
- Prefer plain-text widgets for raw content to avoid accidental markdown rendering.
- Keep the first version focused on 24-hour troubleshooting only. Do not add export, download, or search unless a new requirement appears.
