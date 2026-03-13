# External Platform Upload Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a separate `[6]` external-platform upload workflow that logs into Munpia and Novelpia, creates works when needed, uploads episodes from local files, applies publish options, and runs on its own scheduled queue independent from `[5]`.

**Architecture:** Reuse the existing automation pattern but create a fully separate publishing store, runtime, UI tab, and platform adapter layer. `[5]` continues to generate and save drafts locally; `[6]` reads saved chapter files and drives site-specific browser automation through common client interfaces.

**Tech Stack:** Python, Streamlit, unittest, keyring, Playwright-driven browser automation

---

## File Map

- Modify: `ui/app.py`
  - Register the new `[6]` tab and extend session keys if needed.
- Create: `ui/publishing.py`
  - Render the external upload settings, queue editor, runtime status, and history view.
- Create: `core/publishing_store.py`
  - Persist project-level publishing config, queue, runtime, and history.
- Create: `core/publishing_runtime.py`
  - Schedule due jobs, select pending work, execute platform uploads, and record results.
- Create: `core/platform_credentials.py`
  - Store and load per-platform credentials through keyring.
- Create: `core/chapter_source.py`
  - Resolve source files, load text, and normalize chapter body/title inputs.
- Create: `core/platform_clients/base.py`
  - Define the platform client contract and common result payloads/errors.
- Create: `core/platform_clients/munpia.py`
  - Implement Munpia login, work creation, episode upload, and publish option handling.
- Create: `core/platform_clients/novelpia.py`
  - Implement Novelpia login, work creation, episode upload, and publish option handling.
- Create or Modify: `tests/test_publishing_store.py`
  - Cover config defaults, queue persistence, runtime persistence, and history loading.
- Create or Modify: `tests/test_publishing_runtime.py`
  - Cover scheduling, partial success, retries, pause behavior, and history output.
- Create or Modify: `tests/test_publishing_ui.py`
  - Cover summary formatting, queue row helpers, and status helpers.
- Modify: `tests/test_ui_helpers.py`
  - Verify `[6]` tab ordering and labels.

## Chunk 1: Data Model and Store Foundation

### Task 1: Add failing tests for a dedicated publishing store

**Files:**
- Create: `tests/test_publishing_store.py`
- Create: `core/publishing_store.py`

- [ ] **Step 1: Inspect existing automation store tests and patterns**

Run: `Get-Content tests/test_automation_store.py`
Expected: confirm how project-local JSON persistence is currently tested.

- [ ] **Step 2: Write a failing test for publishing config defaults**

```python
def test_load_config_returns_default_publishing_config():
    store = PublishingStore(project_name="sample")
    config = store.load_config()

    assert config["enabled"] is False
    assert config["platforms"]["munpia"]["enabled"] is False
    assert config["platforms"]["novelpia"]["enabled"] is False
```

- [ ] **Step 3: Add failing tests for queue/runtime/history persistence**

```python
def test_save_and_load_queue_round_trip():
    ...

def test_save_and_load_runtime_round_trip():
    ...

def test_append_history_and_load_recent_history():
    ...
```

- [ ] **Step 4: Run the focused store tests**

Run: `python -m unittest tests.test_publishing_store -v`
Expected: FAIL because `PublishingStore` does not exist yet.

- [ ] **Step 5: Implement the minimal store**

Create `core/publishing_store.py` with:
- default config payload
- `publishing_dir`, `config_path`, `queue_path`, `runtime_path`, `history_path`
- `load_config`, `save_config`, `load_queue`, `save_queue`, `load_runtime`, `save_runtime`, `append_history`, `load_recent_history`

- [ ] **Step 6: Re-run the focused store tests**

Run: `python -m unittest tests.test_publishing_store -v`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add core/publishing_store.py tests/test_publishing_store.py
git commit -m "feat: add publishing store foundation"
```

### Task 2: Add failing tests for publishing helper defaults and queue rows

**Files:**
- Create: `tests/test_publishing_ui.py`
- Create: `ui/publishing.py`

- [ ] **Step 1: Write failing tests for helper formatting**

```python
def test_format_publishing_schedule_summary_for_daily_rule():
    ...

def test_build_publishing_queue_rows_handles_partial_platform_selection():
    ...

def test_format_publishing_runtime_status_reports_paused_error():
    ...
```

- [ ] **Step 2: Run the focused UI helper tests**

Run: `python -m unittest tests.test_publishing_ui -v`
Expected: FAIL because the module or helpers do not exist yet.

- [ ] **Step 3: Implement helper-only UI module skeleton**

In `ui/publishing.py`, add:
- schedule summary formatter
- runtime status formatter
- queue row builder
- history summary helper

Do not render the full tab yet.

- [ ] **Step 4: Re-run the helper tests**

Run: `python -m unittest tests.test_publishing_ui -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add ui/publishing.py tests/test_publishing_ui.py
git commit -m "test: add publishing ui helper coverage"
```

## Chunk 2: Tab Wiring and Credential Storage

### Task 3: Add failing tests for `[6]` tab registration

**Files:**
- Modify: `tests/test_ui_helpers.py`
- Modify: `ui/app.py`

- [ ] **Step 1: Extend the tab-label test with the new tab**

```python
self.assertEqual(
    PROJECT_TAB_LABELS,
    (
        "[1] 프로젝트 통합 설정",
        "[2] 회차 생성",
        "[3] 원고 검수",
        "[4] 반자동 연재 모드",
        "[5] 자동화 연재 모드",
        "[6] 외부 플랫폼 업로드",
    ),
)
```

- [ ] **Step 2: Run the focused helper tests**

Run: `python -m unittest tests.test_ui_helpers -v`
Expected: FAIL because the tab list has not been extended.

- [ ] **Step 3: Update `ui/app.py` minimally**

Add:
- the new tab label
- import for `render_publishing_tab`
- one additional `st.tabs(...)` target

Keep the body of the new tab minimal until the render function is ready.

- [ ] **Step 4: Re-run the focused helper tests**

Run: `python -m unittest tests.test_ui_helpers -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add ui/app.py tests/test_ui_helpers.py
git commit -m "feat: register external platform upload tab"
```

### Task 4: Add failing tests for platform credential storage

**Files:**
- Create: `core/platform_credentials.py`
- Create or Modify: `tests/test_platform_credentials.py`

- [ ] **Step 1: Write failing tests around a fake keyring backend**

```python
def test_save_and_load_munpia_credentials():
    ...

def test_load_missing_credentials_returns_empty_payload():
    ...
```

- [ ] **Step 2: Run the focused credential tests**

Run: `python -m unittest tests.test_platform_credentials -v`
Expected: FAIL because the module does not exist yet.

- [ ] **Step 3: Implement the minimal credential wrapper**

Expose helpers such as:
- `save_platform_credentials(project_name, platform_name, username, password)`
- `load_platform_credentials(project_name, platform_name)`
- `clear_platform_credentials(project_name, platform_name)`

- [ ] **Step 4: Re-run the credential tests**

Run: `python -m unittest tests.test_platform_credentials -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add core/platform_credentials.py tests/test_platform_credentials.py
git commit -m "feat: add platform credential storage"
```

## Chunk 3: Runtime Scheduling and Status Aggregation

### Task 5: Add failing tests for publishing runtime scheduling

**Files:**
- Create: `core/publishing_runtime.py`
- Create: `tests/test_publishing_runtime.py`

- [ ] **Step 1: Write failing tests for due-job execution**

```python
def test_tick_skips_when_publishing_is_disabled():
    ...

def test_tick_runs_first_pending_job_when_schedule_is_due():
    ...
```

- [ ] **Step 2: Add failing tests for partial success and pause behavior**

```python
def test_tick_marks_partial_failed_when_only_one_platform_succeeds():
    ...

def test_tick_pauses_runtime_on_requires_user_action_error():
    ...
```

- [ ] **Step 3: Run the focused runtime tests**

Run: `python -m unittest tests.test_publishing_runtime -v`
Expected: FAIL because the runtime does not exist yet.

- [ ] **Step 4: Implement the runtime minimally**

In `core/publishing_runtime.py`, add:
- default runtime state
- `PublishingRuntime.tick()`
- queue selection
- overall status aggregation from per-platform results
- history append behavior

Stub the actual platform work behind an injected executor interface first.

- [ ] **Step 5: Re-run the focused runtime tests**

Run: `python -m unittest tests.test_publishing_runtime -v`
Expected: PASS for scheduling and status aggregation behavior.

- [ ] **Step 6: Commit**

```bash
git add core/publishing_runtime.py tests/test_publishing_runtime.py
git commit -m "feat: add publishing runtime scheduling"
```

### Task 6: Add chapter-source loading tests and minimal implementation

**Files:**
- Create: `core/chapter_source.py`
- Create or Modify: `tests/test_chapter_source.py`

- [ ] **Step 1: Write failing tests for source loading**

```python
def test_load_chapter_source_reads_markdown_file():
    ...

def test_load_chapter_source_rejects_missing_file():
    ...
```

- [ ] **Step 2: Run the focused source tests**

Run: `python -m unittest tests.test_chapter_source -v`
Expected: FAIL because the module does not exist yet.

- [ ] **Step 3: Implement minimal source loading**

Add helpers for:
- resolving a project-relative source path
- reading UTF-8 text
- deriving a fallback title from file content or filename

- [ ] **Step 4: Re-run the focused source tests**

Run: `python -m unittest tests.test_chapter_source -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add core/chapter_source.py tests/test_chapter_source.py
git commit -m "feat: add chapter source loader for publishing"
```

## Chunk 4: Platform Client Contracts

### Task 7: Add a base platform client contract and fake-driven tests

**Files:**
- Create: `core/platform_clients/base.py`
- Modify: `tests/test_publishing_runtime.py`

- [ ] **Step 1: Define the shared contract in tests first**

Add fake classes or typed payload expectations for:
- login result
- work creation result
- episode upload result
- structured platform errors with `retryable`, `requires_user_action`, `permanent`

- [ ] **Step 2: Run the runtime tests**

Run: `python -m unittest tests.test_publishing_runtime -v`
Expected: FAIL or remain incomplete until the contract exists.

- [ ] **Step 3: Implement `base.py`**

Add:
- dataclasses for `PlatformWorkMetadata`, `EpisodeUploadRequest`, `PlatformActionResult`
- custom exceptions for classified failures
- abstract client methods: `login`, `ensure_work`, `upload_episode`

- [ ] **Step 4: Re-run the runtime tests**

Run: `python -m unittest tests.test_publishing_runtime -v`
Expected: PASS with the shared types in place.

- [ ] **Step 5: Commit**

```bash
git add core/platform_clients/base.py tests/test_publishing_runtime.py
git commit -m "feat: add platform client base contract"
```

## Chunk 5: Munpia Client

### Task 8: Scaffold Munpia client with login and upload flow under fake browser tests

**Files:**
- Create: `core/platform_clients/munpia.py`
- Create or Modify: `tests/test_munpia_client.py`

- [ ] **Step 1: Write failing tests for request building and error classification**

```python
def test_munpia_client_requires_credentials_before_login():
    ...

def test_munpia_client_maps_missing_editor_field_to_retryable_error():
    ...
```

- [ ] **Step 2: Run the focused Munpia client tests**

Run: `python -m unittest tests.test_munpia_client -v`
Expected: FAIL because the client does not exist yet.

- [ ] **Step 3: Implement a minimal Munpia client skeleton**

Add methods for:
- opening the login page
- filling username/password
- classifying login failures
- placeholder methods for work creation and episode upload

Keep browser actions behind injectable helpers so unit tests do not hit the real site.

- [ ] **Step 4: Re-run the focused tests**

Run: `python -m unittest tests.test_munpia_client -v`
Expected: PASS for the helper-level behaviors.

- [ ] **Step 5: Commit**

```bash
git add core/platform_clients/munpia.py tests/test_munpia_client.py
git commit -m "feat: scaffold munpia publishing client"
```

### Task 9: Extend Munpia client to work creation and episode upload

**Files:**
- Modify: `core/platform_clients/munpia.py`
- Modify: `tests/test_munpia_client.py`

- [ ] **Step 1: Add failing tests for work-id extraction and upload payload mapping**

```python
def test_ensure_work_returns_existing_work_id_when_present():
    ...

def test_upload_episode_returns_episode_id_on_success():
    ...
```

- [ ] **Step 2: Run the focused tests**

Run: `python -m unittest tests.test_munpia_client -v`
Expected: FAIL before the methods are implemented.

- [ ] **Step 3: Implement the minimal flow**

Handle:
- existing `work_id`
- new work creation path
- episode title/body input
- publish visibility and reservation mapping

- [ ] **Step 4: Re-run the focused tests**

Run: `python -m unittest tests.test_munpia_client -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add core/platform_clients/munpia.py tests/test_munpia_client.py
git commit -m "feat: add munpia work creation and episode upload"
```

## Chunk 6: Novelpia Client

### Task 10: Scaffold Novelpia client with login and upload flow under fake browser tests

**Files:**
- Create: `core/platform_clients/novelpia.py`
- Create or Modify: `tests/test_novelpia_client.py`

- [ ] **Step 1: Write failing tests for credential handling and login classification**

```python
def test_novelpia_client_requires_credentials_before_login():
    ...

def test_novelpia_client_classifies_additional_auth_as_user_action():
    ...
```

- [ ] **Step 2: Run the focused Novelpia tests**

Run: `python -m unittest tests.test_novelpia_client -v`
Expected: FAIL because the client does not exist yet.

- [ ] **Step 3: Implement a minimal Novelpia client skeleton**

Support:
- CP login entry
- username/password fill
- error classification
- placeholder methods for work creation and episode upload

- [ ] **Step 4: Re-run the focused tests**

Run: `python -m unittest tests.test_novelpia_client -v`
Expected: PASS at helper level.

- [ ] **Step 5: Commit**

```bash
git add core/platform_clients/novelpia.py tests/test_novelpia_client.py
git commit -m "feat: scaffold novelpia publishing client"
```

### Task 11: Extend Novelpia client to work creation and episode upload

**Files:**
- Modify: `core/platform_clients/novelpia.py`
- Modify: `tests/test_novelpia_client.py`

- [ ] **Step 1: Add failing tests for work creation and episode result parsing**

```python
def test_ensure_work_returns_created_work_id():
    ...

def test_upload_episode_returns_success_payload():
    ...
```

- [ ] **Step 2: Run the focused tests**

Run: `python -m unittest tests.test_novelpia_client -v`
Expected: FAIL before the behavior exists.

- [ ] **Step 3: Implement the minimal work/create upload flow**

Support:
- existing `work_id`
- work creation path
- episode editor fill
- publish mode and visibility mapping

- [ ] **Step 4: Re-run the focused tests**

Run: `python -m unittest tests.test_novelpia_client -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add core/platform_clients/novelpia.py tests/test_novelpia_client.py
git commit -m "feat: add novelpia work creation and episode upload"
```

## Chunk 7: Full UI Rendering and Runtime Wiring

### Task 12: Render the full `[6]` tab and wire it to the publishing store

**Files:**
- Modify: `ui/publishing.py`
- Modify: `ui/app.py`
- Modify: `core/publishing_store.py`

- [ ] **Step 1: Add failing tests for UI helper outputs needed by the full tab**

Extend `tests/test_publishing_ui.py` with helpers covering:
- platform selection summary
- queue pending count
- history success/failure totals

- [ ] **Step 2: Run the focused UI tests**

Run: `python -m unittest tests.test_publishing_ui -v`
Expected: FAIL before helpers are complete.

- [ ] **Step 3: Implement the full rendering flow**

In `ui/publishing.py`, render:
- platform credential inputs and save actions
- work metadata inputs and create-work actions
- schedule editor
- queue add/edit controls
- runtime summary
- recent history table

- [ ] **Step 4: Wire the tab in `ui/app.py`**

Ensure the new tab calls `render_publishing_tab(app)` and does not disturb tabs `[1]` through `[5]`.

- [ ] **Step 5: Re-run the UI tests**

Run: `python -m unittest tests.test_publishing_ui tests.test_ui_helpers -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add ui/publishing.py ui/app.py core/publishing_store.py tests/test_publishing_ui.py tests/test_ui_helpers.py
git commit -m "feat: add publishing tab ui"
```

### Task 13: Wire runtime background polling for publishing jobs

**Files:**
- Modify: `ui/app.py`
- Modify: `core/publishing_runtime.py`
- Modify: `tests/test_publishing_runtime.py`

- [ ] **Step 1: Add failing tests for project-level runtime scanning**

```python
def test_run_publishing_pass_only_executes_enabled_projects():
    ...
```

- [ ] **Step 2: Run the focused runtime tests**

Run: `python -m unittest tests.test_publishing_runtime -v`
Expected: FAIL before the project-scanning helper exists.

- [ ] **Step 3: Implement the background pass helper**

Add a project scan similar to the existing automation background loop and start it from `ui/app.py`.

- [ ] **Step 4: Re-run the runtime tests**

Run: `python -m unittest tests.test_publishing_runtime -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add core/publishing_runtime.py ui/app.py tests/test_publishing_runtime.py
git commit -m "feat: add publishing background scheduler"
```

## Chunk 8: Verification and Manual Browser Checks

### Task 14: Run the relevant automated tests

**Files:**
- Modify if needed: `tests/test_publishing_store.py`
- Modify if needed: `tests/test_publishing_runtime.py`
- Modify if needed: `tests/test_publishing_ui.py`
- Modify if needed: `tests/test_ui_helpers.py`

- [ ] **Step 1: Run the publishing-focused suite**

Run: `python -m unittest tests.test_publishing_store tests.test_publishing_runtime tests.test_publishing_ui tests.test_ui_helpers tests.test_platform_credentials tests.test_chapter_source tests.test_munpia_client tests.test_novelpia_client -v`
Expected: PASS.

- [ ] **Step 2: Run existing automation smoke tests for regression coverage**

Run: `python -m unittest tests.test_automation_store tests.test_automation_runtime tests.test_automation_ui -v`
Expected: PASS with no regressions in `[5]`.

- [ ] **Step 3: If a test fails, fix only the failing scope and re-run the exact test before broadening again**

Expected: clean focused reruns before returning to full suites.

- [ ] **Step 4: Commit**

```bash
git add core ui tests
git commit -m "test: verify publishing automation flow"
```

### Task 15: Perform manual site verification with headed browser runs

**Files:**
- No committed file changes expected unless selectors or error handling need adjustment

- [ ] **Step 1: Launch the app locally**

Run: `streamlit run ui/app.py`
Expected: app opens with a `[6] 외부 플랫폼 업로드` tab.

- [ ] **Step 2: Verify Munpia happy path manually**

Expected:
- credentials save
- login succeeds
- new work creation succeeds
- episode upload succeeds
- runtime/history update correctly

- [ ] **Step 3: Verify Novelpia happy path manually**

Expected:
- credentials save
- CP login succeeds
- new work creation succeeds
- episode upload succeeds
- runtime/history update correctly

- [ ] **Step 4: Verify failure behavior manually**

Expected:
- wrong password pauses runtime
- one-platform failure yields `partial_failed`
- missing source file marks job failed without crashing the runtime

- [ ] **Step 5: Commit any selector/error-handling fixes discovered during manual validation**

```bash
git add core/platform_clients ui/publishing.py tests
git commit -m "fix: harden publishing platform automation"
```

Plan complete and saved to `docs/superpowers/plans/2026-03-13-external-platform-upload.md`. Ready to execute?
