# Community Cloud Manual Mode Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Community Cloud runtime mode that persists project files through a GitHub-backed storage backend and hides workstation-only features so the app works as a manual/semi-auto hosted tool.

**Architecture:** Introduce runtime-mode and storage abstractions first, then route project persistence through those abstractions while preserving the existing local backend. After storage is in place, gate background services and UI affordances behind runtime-mode checks so Community Cloud only exposes supported workflows.

**Tech Stack:** Python, Streamlit, unittest, existing file-based project model, GitHub Contents API

---

## File Map

- Create: `core/runtime.py`
  - Central runtime-mode detection and cloud feature flags.
- Create: `core/storage.py`
  - Shared storage protocol and backend factory helpers.
- Create: `core/github_storage.py`
  - GitHub-backed project storage implementation.
- Modify: `core/context.py`
  - Replace direct project-file reads/writes with the storage abstraction.
- Modify: `core/generator.py`
  - Route markdown saves/listing through storage-aware behavior.
- Modify: `core/api_key_store.py`
  - Respect cloud restrictions around secure/local storage features.
- Modify: `ui/app.py`
  - Gate background services, banner, and tab visibility based on runtime mode.
- Modify: `ui/chapters.py`
  - Hide local path/folder-open UX in cloud mode and adjust save messaging.
- Modify: `ui/workspace.py`
  - Hide `.env`, `keyring`, and Gemini CLI controls in cloud mode.
- Create or Modify: `tests/test_runtime.py`
  - Cover runtime-mode detection and cloud requirements.
- Create or Modify: `tests/test_context_manager.py`
  - Verify storage-backed config/character persistence in both modes.
- Create or Modify: `tests/test_generator_storage.py`
  - Verify markdown save/list behavior through the storage abstraction.
- Create or Modify: `tests/test_ui_helpers.py`
  - Cover cloud-mode UI helper logic if small helpers are extracted.

## Chunk 1: Runtime Mode Foundation

### Task 1: Add failing tests for runtime-mode detection

**Files:**
- Create or Modify: `tests/test_runtime.py`
- Create: `core/runtime.py`

- [ ] **Step 1: Write a failing test for default local mode**

```python
def test_get_runtime_mode_defaults_to_local():
    with patch.dict(os.environ, {}, clear=True):
        assert module.get_runtime_mode() == "local"
```

- [ ] **Step 2: Write a failing test for Community Cloud mode**

```python
def test_get_runtime_mode_reads_community_cloud_env():
    with patch.dict(os.environ, {"APP_RUNTIME": "community_cloud"}, clear=True):
        assert module.get_runtime_mode() == "community_cloud"
```

- [ ] **Step 3: Run the focused tests and verify RED**

Run: `python -m unittest tests.test_runtime -v`
Expected: FAIL because `core.runtime` does not exist yet.

- [ ] **Step 4: Implement minimal runtime detection**

```python
def get_runtime_mode() -> str:
    value = os.getenv("APP_RUNTIME", "local").strip().lower()
    return "community_cloud" if value == "community_cloud" else "local"
```

- [ ] **Step 5: Re-run the focused tests and verify GREEN**

Run: `python -m unittest tests.test_runtime -v`
Expected: PASS.

### Task 2: Add failing tests for cloud feature flags

**Files:**
- Modify: `tests/test_runtime.py`
- Modify: `core/runtime.py`

- [ ] **Step 1: Add a failing test for restricted cloud behavior**

```python
def test_is_cloud_runtime_true_only_for_community_cloud():
    with patch.dict(os.environ, {"APP_RUNTIME": "community_cloud"}, clear=True):
        assert module.is_cloud_runtime() is True
```

- [ ] **Step 2: Add a failing test for required GitHub storage settings**

```python
def test_validate_cloud_storage_settings_raises_when_missing():
    with patch.dict(os.environ, {"APP_RUNTIME": "community_cloud"}, clear=True):
        with self.assertRaises(RuntimeError):
            module.validate_cloud_storage_settings()
```

- [ ] **Step 3: Run the focused tests and verify RED**

Run: `python -m unittest tests.test_runtime -v`
Expected: FAIL because helpers do not exist yet.

- [ ] **Step 4: Implement minimal helpers**

Add:
- `is_cloud_runtime()`
- `get_cloud_storage_repo()`
- `get_cloud_storage_token()`
- `validate_cloud_storage_settings()`

- [ ] **Step 5: Re-run the focused tests and verify GREEN**

Run: `python -m unittest tests.test_runtime -v`
Expected: PASS.

## Chunk 2: Storage Abstraction

### Task 3: Add failing tests for storage-backed context persistence

**Files:**
- Modify: `tests/test_context_manager.py`
- Create: `core/storage.py`
- Modify: `core/context.py`

- [ ] **Step 1: Inspect existing context tests**

Run: `rg -n "ContextManager|save_config|save_characters" tests/test_context_manager.py`
Expected: locate current file-based tests to extend rather than duplicate.

- [ ] **Step 2: Add a failing test for storage-backed config persistence**

```python
def test_context_manager_uses_storage_backend_for_config_round_trip():
    storage = InMemoryProjectStorage()
    manager = ContextManager(project_name="sample", storage=storage)
    manager.save_config({"worldview": "x"})
    assert manager.get_config()["worldview"] == "x"
```

- [ ] **Step 3: Add a failing test for storage-backed characters persistence**

```python
def test_context_manager_uses_storage_backend_for_characters_round_trip():
    ...
```

- [ ] **Step 4: Run the focused tests and verify RED**

Run: `python -m unittest tests.test_context_manager -v`
Expected: FAIL because `ContextManager` does not accept injected storage yet.

- [ ] **Step 5: Implement the shared storage protocol and in-memory test backend**

Add a minimal protocol in `core/storage.py` and allow `ContextManager(..., storage=...)`.

- [ ] **Step 6: Re-run the focused tests and verify GREEN**

Run: `python -m unittest tests.test_context_manager -v`
Expected: PASS.

### Task 4: Add failing tests for markdown saves through storage-aware generator behavior

**Files:**
- Modify: `tests/test_generator_storage.py`
- Modify: `core/generator.py`
- Modify: `core/storage.py`

- [ ] **Step 1: Add a failing test for saved markdown landing in backend storage**

```python
def test_save_markdown_document_writes_to_storage_backend():
    storage = InMemoryProjectStorage()
    generator = Generator(project_name="sample", storage=storage)
    saved_path = generator.save_markdown_document("1화", "본문")
    assert storage.read_text("sample", "chapters/1화.md").startswith("# 1화")
```

- [ ] **Step 2: Run the focused tests and verify RED**

Run: `python -m unittest tests.test_generator_storage -v`
Expected: FAIL because `Generator` still writes directly to disk.

- [ ] **Step 3: Implement minimal storage-aware markdown save/list behavior**

Keep local backend behavior intact, but allow injected storage to handle file writes and chapter listing.

- [ ] **Step 4: Re-run the focused tests and verify GREEN**

Run: `python -m unittest tests.test_generator_storage -v`
Expected: PASS.

## Chunk 3: GitHub Backend

### Task 5: Add failing tests for GitHub-backed storage request shaping

**Files:**
- Create or Modify: `tests/test_github_storage.py`
- Create: `core/github_storage.py`

- [ ] **Step 1: Add a failing test for reading a file from GitHub**

```python
def test_github_storage_reads_and_decodes_file_contents():
    ...
```

- [ ] **Step 2: Add a failing test for writing a file to GitHub**

```python
def test_github_storage_puts_base64_encoded_content_with_sha_when_updating():
    ...
```

- [ ] **Step 3: Run the focused tests and verify RED**

Run: `python -m unittest tests.test_github_storage -v`
Expected: FAIL because backend does not exist yet.

- [ ] **Step 4: Implement minimal GitHub backend**

Use the GitHub Contents API with:
- `GET /repos/{owner}/{repo}/contents/{path}`
- `PUT /repos/{owner}/{repo}/contents/{path}`

Support:
- read text
- write text
- exists
- list paths under a prefix if needed by current UI

- [ ] **Step 5: Re-run the focused tests and verify GREEN**

Run: `python -m unittest tests.test_github_storage -v`
Expected: PASS.

## Chunk 4: Community Cloud UI Restrictions

### Task 6: Add failing tests for cloud tab visibility decisions

**Files:**
- Modify: `tests/test_ui_helpers.py`
- Modify: `ui/app.py`

- [ ] **Step 1: Extract a helper that returns visible project tabs**

```python
def get_project_tab_labels(is_cloud: bool) -> tuple[str, ...]:
    ...
```

- [ ] **Step 2: Add failing tests**

```python
def test_get_project_tab_labels_hides_automation_and_upload_in_cloud():
    ...
```

- [ ] **Step 3: Run the focused tests and verify RED**

Run: `python -m unittest tests.test_ui_helpers -v`
Expected: FAIL before helper exists.

- [ ] **Step 4: Implement minimal helper and wire `ui/app.py`**

Also:
- skip `get_automation_background_service()`
- skip `get_publishing_background_service()`
- show a cloud-mode banner

- [ ] **Step 5: Re-run the focused tests and verify GREEN**

Run: `python -m unittest tests.test_ui_helpers -v`
Expected: PASS.

### Task 7: Add failing tests for cloud-save/local-path UI helper behavior

**Files:**
- Modify: `tests/test_ui_helpers.py`
- Modify: `ui/chapters.py`

- [ ] **Step 1: Extract helpers for cloud-safe save messaging and folder controls**

```python
def should_show_local_folder_actions(is_cloud: bool) -> bool:
    return not is_cloud

def format_saved_document_notice(saved_path: str, is_cloud: bool) -> str:
    ...
```

- [ ] **Step 2: Add failing tests**

```python
def test_should_show_local_folder_actions_false_in_cloud():
    ...

def test_format_saved_document_notice_uses_cloud_message():
    ...
```

- [ ] **Step 3: Run the focused tests and verify RED**

Run: `python -m unittest tests.test_ui_helpers -v`
Expected: FAIL before helpers exist.

- [ ] **Step 4: Implement minimal helpers and wire save/folder UI**

Hide:
- path hints
- folder-open buttons

Adjust:
- save success text

- [ ] **Step 5: Re-run the focused tests and verify GREEN**

Run: `python -m unittest tests.test_ui_helpers -v`
Expected: PASS.

### Task 8: Add failing tests for cloud API settings restrictions

**Files:**
- Modify: `tests/test_ui_helpers.py`
- Modify: `ui/workspace.py`

- [ ] **Step 1: Extract a helper that describes allowed API controls in cloud mode**

```python
def get_api_settings_mode(is_cloud: bool) -> dict[str, bool]:
    ...
```

- [ ] **Step 2: Add failing tests**

```python
def test_get_api_settings_mode_disables_keyring_env_and_cli_in_cloud():
    ...
```

- [ ] **Step 3: Run the focused tests and verify RED**

Run: `python -m unittest tests.test_ui_helpers -v`
Expected: FAIL before helper exists.

- [ ] **Step 4: Implement minimal helper and wire API settings UI**

Hide or disable in cloud mode:
- secure storage save/delete
- `.env` persistence
- Gemini CLI diagnostics/test controls

- [ ] **Step 5: Re-run the focused tests and verify GREEN**

Run: `python -m unittest tests.test_ui_helpers -v`
Expected: PASS.

## Chunk 5: Verification

### Task 9: Run focused regression checks

**Files:**
- Modify if needed: `tests/test_runtime.py`
- Modify if needed: `tests/test_context_manager.py`
- Modify if needed: `tests/test_generator_storage.py`
- Modify if needed: `tests/test_github_storage.py`
- Modify if needed: `tests/test_ui_helpers.py`

- [ ] **Step 1: Run the focused suite**

Run: `python -m unittest tests.test_runtime tests.test_context_manager tests.test_generator_storage tests.test_github_storage tests.test_ui_helpers -v`
Expected: PASS.

- [ ] **Step 2: Run a broader regression suite around writing flow**

Run: `python -m unittest tests.test_automator tests.test_publishing_store tests.test_diagnostics tests.test_model_catalog -v`
Expected: PASS.

- [ ] **Step 3: Run a local smoke check**

Run: `python -m streamlit run main.py --server.headless true`
Expected: app starts without immediate import/runtime errors.

- [ ] **Step 4: Create a dedicated deployment branch**

Run: `git checkout -b community-cloud-manual-mode`
Expected: new branch created for hosted deployment work.

Plan complete and saved to `docs/superpowers/plans/2026-03-19-community-cloud-manual-mode.md`. Ready to execute?
