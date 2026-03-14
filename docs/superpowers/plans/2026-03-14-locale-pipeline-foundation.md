# Locale Pipeline Foundation Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deferred locale pipeline foundation that starts from successfully published Korean episodes, creates per-locale source bundles and translation jobs, runs locale-specific translation and quality gates, and stores locale-ready artifacts without yet automating foreign-site uploads.

**Architecture:** Reuse the existing `store -> runtime -> executor -> UI` pattern already used by automation and publishing. Korean origin publication remains the single source of truth; successful Korean publication emits locale handoff records, and each locale runs its own isolated queue, runtime state, glossary/style guide, translation artifacts, and incident history under `data/projects/<project>/translations/<locale>/`.

**Tech Stack:** Python, unittest, Streamlit, existing LLM backend interfaces, JSON/JSONL project stores

---

## Scope Note

This plan intentionally stops at `locale publishable artifacts + locale publish queue records`. It does **not** implement real overseas site automation yet.

Reasons:
- overseas target sites are not fixed yet
- foreign-site selectors/login flows are independent subsystems
- keeping this plan focused makes later execution safer and testable

Follow-up plans should be created later per concrete destination platform, for example:
- `Royal Road adapter`
- `Scribble Hub adapter`
- `Japanese platform adapter`

## File Map

- Create: `core/locale_store.py`
  - Persist project-level locale config, locale translation queue, locale publish queue, runtime, source bundles, and history under `data/projects/<project>/translations/<locale>/`.
- Create: `core/locale_bundle.py`
  - Build a stable locale source bundle from a published Korean episode, canon snapshot, glossary version, and character sheet metadata.
- Create: `core/locale_handoff.py`
  - Convert successful Korean publication records into pending locale translation jobs for enabled locales.
- Create: `core/locale_quality.py`
  - Run rule-based locale checks on translated output before it becomes publishable.
- Create: `core/locale_executor.py`
  - Execute one locale translation job: load source bundle, call translation backend, run locale quality checks, write locale draft/publishable files, and enqueue deferred locale publish jobs.
- Create: `core/locale_runtime.py`
  - Poll enabled locales, select pending locale jobs, run executor, update runtime state, and append locale history.
- Create: `ui/localization.py`
  - Render locale settings, glossary/style-guide status, translation queues, publish queues, runtime status, and incident history.
- Modify: `ui/app.py`
  - Register the new locale pipeline tab.
- Modify: `core/publishing_runtime.py`
  - Trigger locale handoff only after Korean origin publication succeeds.
- Modify: `core/model_catalog.py`
  - Add optional locale translation model policy metadata if no suitable selector exists yet.
- Create: `tests/test_locale_store.py`
  - Cover locale config defaults, per-locale path layout, queue/runtime persistence, and history loading.
- Create: `tests/test_locale_bundle.py`
  - Cover source bundle generation from a published Korean episode.
- Create: `tests/test_locale_handoff.py`
  - Cover origin publication to locale queue fan-out rules.
- Create: `tests/test_locale_quality.py`
  - Cover glossary enforcement, missing-name detection, and blocked locale output patterns.
- Create: `tests/test_locale_executor.py`
  - Cover successful translation, failed quality gate, and deferred publish queue creation.
- Create: `tests/test_locale_runtime.py`
  - Cover scheduling, retries, stop states, and per-locale isolation.
- Create: `tests/test_localization_ui.py`
  - Cover locale UI helper formatting and queue/history summaries.
- Modify: `tests/test_ui_helpers.py`
  - Verify the new locale pipeline tab label and order.

## Data Layout Target

The implementation should converge on this per-project structure:

```text
data/projects/<project>/
  episodes/
    published/ko-KR/
      ep_038.md
  canon/
    snapshots/
      ep_038.json
  translations/
    en-US/
      config.json
      runtime.json
      translation_queue.json
      publish_queue.json
      history.jsonl
      glossary.json
      style_guide.md
      bundles/
        ep_038.json
      drafts/
        ep_038.en-US.md
      publishable/
        ep_038.en-US.md
      incidents/
        2026-03-14.jsonl
    ja-JP/
      ...
```

`episodes/published/ko-KR/` remains the origin source of truth. Locale output never updates the Korean canon or Korean origin queue.

## Chunk 1: Locale Store and Source Bundles

### Task 1: Add failing tests for per-locale store defaults and path layout

**Files:**
- Create: `tests/test_locale_store.py`
- Create: `core/locale_store.py`

- [ ] **Step 1: Inspect existing store patterns**

Run: `python -m unittest tests.test_automation_store tests.test_publishing_store -v`
Expected: confirm the store contract and default payload style already used in the codebase.

- [ ] **Step 2: Write failing tests for locale config defaults**

```python
def test_load_locale_config_returns_default_payload():
    store = LocaleStore(project_name="sample", locale_code="en-US")
    config = store.load_config()

    assert config["enabled"] is False
    assert config["source_locale"] == "ko-KR"
    assert config["target_locale"] == "en-US"
    assert config["translation_model"] != ""
    assert config["publish_enabled"] is False
```

- [ ] **Step 3: Add failing tests for queue/runtime/history round trips**

```python
def test_save_and_load_translation_queue_round_trip():
    ...

def test_save_and_load_publish_queue_round_trip():
    ...

def test_save_and_load_runtime_round_trip():
    ...

def test_append_and_load_locale_history():
    ...
```

- [ ] **Step 4: Run the focused locale store tests**

Run: `python -m unittest tests.test_locale_store -v`
Expected: FAIL because `LocaleStore` does not exist yet.

- [ ] **Step 5: Implement the minimal locale store**

Create `core/locale_store.py` with:
- `DEFAULT_LOCALE_CONFIG`
- per-locale directory properties for `bundles`, `drafts`, `publishable`, `incidents`
- `load_config`, `save_config`
- `load_translation_queue`, `save_translation_queue`
- `load_publish_queue`, `save_publish_queue`
- `load_runtime`, `save_runtime`
- `append_history`, `load_recent_history`

- [ ] **Step 6: Re-run the locale store tests**

Run: `python -m unittest tests.test_locale_store -v`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add core/locale_store.py tests/test_locale_store.py
git commit -m "feat: add locale store foundation"
```

### Task 2: Add failing tests for locale source bundle generation

**Files:**
- Create: `tests/test_locale_bundle.py`
- Create: `core/locale_bundle.py`

- [ ] **Step 1: Write failing tests for a stable source bundle**

```python
def test_build_locale_bundle_reads_published_korean_episode_and_canon_snapshot():
    bundle = build_locale_bundle(
        project_name="sample",
        episode_id="ep_038",
        source_locale="ko-KR",
        target_locale="en-US",
    )

    assert bundle["episode_id"] == "ep_038"
    assert bundle["source_locale"] == "ko-KR"
    assert bundle["target_locale"] == "en-US"
    assert bundle["source_text"]
    assert bundle["canon_snapshot_path"].endswith("ep_038.json")
```

- [ ] **Step 2: Add a failing test for missing published source**

```python
def test_build_locale_bundle_raises_when_origin_episode_is_not_published():
    ...
```

- [ ] **Step 3: Run the focused bundle tests**

Run: `python -m unittest tests.test_locale_bundle -v`
Expected: FAIL because the bundle builder does not exist yet.

- [ ] **Step 4: Implement the minimal bundle builder**

Include:
- Korean published path resolver
- canon snapshot lookup
- bundle payload writer
- deterministic bundle filename convention

- [ ] **Step 5: Re-run the bundle tests**

Run: `python -m unittest tests.test_locale_bundle -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add core/locale_bundle.py tests/test_locale_bundle.py
git commit -m "feat: add locale source bundle builder"
```

## Chunk 2: Origin-to-Locale Handoff

### Task 3: Add failing tests for locale handoff fan-out after Korean publication

**Files:**
- Create: `tests/test_locale_handoff.py`
- Create: `core/locale_handoff.py`
- Modify: `core/publishing_runtime.py`

- [ ] **Step 1: Write failing tests for enabled locale fan-out**

```python
def test_enqueue_locale_jobs_for_each_enabled_locale_after_origin_publish():
    result = enqueue_locale_jobs_from_origin_publish(
        project_name="sample",
        episode_id="ep_038",
        chapter_title="38화. 계약의 대가",
        locales=[
            {"code": "en-US", "enabled": True},
            {"code": "ja-JP", "enabled": True},
        ],
    )

    assert result["created"] == ["en-US", "ja-JP"]
```

- [ ] **Step 2: Add failing tests for duplicate prevention**

```python
def test_handoff_does_not_duplicate_existing_pending_locale_job():
    ...
```

- [ ] **Step 3: Run the focused handoff tests**

Run: `python -m unittest tests.test_locale_handoff -v`
Expected: FAIL because locale handoff code does not exist yet.

- [ ] **Step 4: Implement `core/locale_handoff.py` minimally**

Expose helpers such as:
- `load_enabled_locales(project_name)`
- `enqueue_locale_jobs_from_origin_publish(...)`

Each created translation job should include:
- `episode_id`
- `source_locale`
- `target_locale`
- `bundle_path`
- `status`
- `attempt_count`
- `created_at`

- [ ] **Step 5: Update `core/publishing_runtime.py` to call locale handoff only on successful Korean publication**

Trigger the handoff only when:
- origin job overall status is `done`
- source locale is `ko-KR`
- the chapter has a canonical episode identifier

Do not call locale handoff on `partial_failed`, `failed`, or manual preview runs.

- [ ] **Step 6: Re-run the focused handoff tests**

Run: `python -m unittest tests.test_locale_handoff -v`
Expected: PASS.

- [ ] **Step 7: Run publishing runtime tests that cover unchanged origin behavior**

Run: `python -m unittest tests.test_publishing_runtime -v`
Expected: PASS with no regression in origin publishing state transitions.

- [ ] **Step 8: Commit**

```bash
git add core/locale_handoff.py core/publishing_runtime.py tests/test_locale_handoff.py
git commit -m "feat: enqueue locale jobs after successful origin publish"
```

## Chunk 3: Locale Translation Quality and Execution

### Task 4: Add failing tests for locale quality gates

**Files:**
- Create: `tests/test_locale_quality.py`
- Create: `core/locale_quality.py`

- [ ] **Step 1: Write failing tests for glossary and blocked-pattern checks**

```python
def test_validate_locale_output_flags_missing_required_glossary_name():
    report = validate_locale_output(
        source_text="이한이 웃었다.",
        translated_text="The protagonist laughed.",
        glossary={"이한": "Lee Han"},
    )

    assert report["status"] == "failed"
    assert "Lee Han" in report["errors"][0]
```

def test_validate_locale_output_flags_blocked_leakage_patterns():
    ...
```

- [ ] **Step 2: Add a passing-case test**

```python
def test_validate_locale_output_passes_for_compliant_translation():
    ...
```

- [ ] **Step 3: Run the focused locale quality tests**

Run: `python -m unittest tests.test_locale_quality -v`
Expected: FAIL because `validate_locale_output` does not exist yet.

- [ ] **Step 4: Implement minimal locale quality checks**

Checks should include:
- required glossary names present
- raw Korean control tokens absent
- repeated untranslated paragraphs absent
- empty or trivially short output rejected

- [ ] **Step 5: Re-run the locale quality tests**

Run: `python -m unittest tests.test_locale_quality -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add core/locale_quality.py tests/test_locale_quality.py
git commit -m "feat: add locale quality gates"
```

### Task 5: Add failing tests for locale executor success and failure paths

**Files:**
- Create: `tests/test_locale_executor.py`
- Create: `core/locale_executor.py`

- [ ] **Step 1: Write a failing success-path test**

```python
def test_execute_locale_job_writes_draft_publishable_and_publish_queue():
    result = executor.execute_translation_job(job)

    assert result["status"] == "publishable"
    assert result["draft_path"].endswith(".en-US.md")
    assert result["publishable_path"].endswith(".en-US.md")
    assert result["publish_job_created"] is True
```

- [ ] **Step 2: Add a failing quality-stop test**

```python
def test_execute_locale_job_stops_when_quality_gate_fails():
    result = executor.execute_translation_job(job)

    assert result["status"] == "failed"
    assert result["publish_job_created"] is False
```

- [ ] **Step 3: Run the focused locale executor tests**

Run: `python -m unittest tests.test_locale_executor -v`
Expected: FAIL because the executor does not exist yet.

- [ ] **Step 4: Implement the minimal executor**

The executor should:
- load the bundle payload
- call the translation backend through the existing LLM abstraction
- write locale draft output
- run `validate_locale_output`
- if valid, write locale publishable output and append a deferred publish queue row
- if invalid, append an incident record and return `failed`

- [ ] **Step 5: Re-run the locale executor tests**

Run: `python -m unittest tests.test_locale_executor -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add core/locale_executor.py tests/test_locale_executor.py
git commit -m "feat: add locale translation executor"
```

### Task 6: Add failing tests for locale runtime scheduling and isolation

**Files:**
- Create: `tests/test_locale_runtime.py`
- Create: `core/locale_runtime.py`
- Modify: `core/model_catalog.py`

- [ ] **Step 1: Write failing runtime tests**

```python
def test_locale_runtime_processes_only_pending_jobs_for_enabled_locale():
    ...

def test_locale_runtime_pauses_on_requires_user_action():
    ...

def test_locale_runtime_failure_does_not_block_other_locales():
    ...
```

- [ ] **Step 2: Run the focused locale runtime tests**

Run: `python -m unittest tests.test_locale_runtime -v`
Expected: FAIL because the runtime does not exist yet.

- [ ] **Step 3: Implement the minimal locale runtime**

Include:
- per-locale `tick(now, force=False)`
- runtime state transitions mirroring publishing runtime
- executor invocation for the next pending locale job
- history append and incident recording

If locale config needs model policy metadata not present in `core/model_catalog.py`, add the smallest possible extension there.

- [ ] **Step 4: Re-run the locale runtime tests**

Run: `python -m unittest tests.test_locale_runtime -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add core/locale_runtime.py core/model_catalog.py tests/test_locale_runtime.py
git commit -m "feat: add locale runtime orchestration"
```

## Chunk 4: Locale UI and Operator Controls

### Task 7: Add failing tests for locale UI helper formatting

**Files:**
- Create: `tests/test_localization_ui.py`
- Create: `ui/localization.py`

- [ ] **Step 1: Write failing helper tests**

```python
def test_format_locale_runtime_status_paused_message():
    ...

def test_build_locale_queue_rows_shows_target_locale_and_attempts():
    ...

def test_build_locale_history_rows_summarizes_quality_failures():
    ...
```

- [ ] **Step 2: Run the focused locale UI tests**

Run: `python -m unittest tests.test_localization_ui -v`
Expected: FAIL because the module does not exist yet.

- [ ] **Step 3: Implement helper-only localization UI module**

Add:
- locale runtime formatter
- locale queue row builder
- locale history row builder
- locale summary helper

Do not render the full Streamlit tab yet.

- [ ] **Step 4: Re-run the locale UI tests**

Run: `python -m unittest tests.test_localization_ui -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add ui/localization.py tests/test_localization_ui.py
git commit -m "test: add locale ui helpers"
```

### Task 8: Add failing tests for the locale pipeline tab and render it

**Files:**
- Modify: `tests/test_ui_helpers.py`
- Modify: `ui/app.py`
- Modify: `ui/localization.py`

- [ ] **Step 1: Extend tab-label coverage**

Add the locale tab after publishing:

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
        "[7] 로케일 파이프라인",
    ),
)
```

- [ ] **Step 2: Run the focused UI helper tests**

Run: `python -m unittest tests.test_ui_helpers -v`
Expected: FAIL because the tab list is not extended yet.

- [ ] **Step 3: Implement tab wiring in `ui/app.py`**

Add:
- `render_localization_tab` import
- one new `st.tabs(...)` target
- stable session keys if the tab needs them

- [ ] **Step 4: Expand `ui/localization.py` to render the real tab**

The first implementation should include:
- locale enable/disable toggles
- translation model selection
- glossary/status indicators
- translation queue table
- deferred publish queue table
- runtime and recent incidents

Avoid adding real foreign-site adapter controls here. This tab is for locale pipeline management only.

- [ ] **Step 5: Re-run the focused UI helper tests**

Run: `python -m unittest tests.test_ui_helpers tests.test_localization_ui -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add ui/app.py ui/localization.py tests/test_ui_helpers.py
git commit -m "feat: add locale pipeline ui tab"
```

## Chunk 5: Verification and Handoff

### Task 9: Verify the locale pipeline foundation end to end

**Files:**
- Verify only

- [ ] **Step 1: Run targeted unit tests**

Run:

```bash
python -m unittest \
  tests.test_locale_store \
  tests.test_locale_bundle \
  tests.test_locale_handoff \
  tests.test_locale_quality \
  tests.test_locale_executor \
  tests.test_locale_runtime \
  tests.test_localization_ui \
  tests.test_ui_helpers \
  -v
```

Expected: PASS.

- [ ] **Step 2: Re-run origin publishing tests to verify no regression**

Run:

```bash
python -m unittest \
  tests.test_publishing_store \
  tests.test_publishing_runtime \
  tests.test_publishing_executor \
  tests.test_publishing_ui \
  -v
```

Expected: PASS.

- [ ] **Step 3: Run lightweight syntax verification**

Run:

```bash
python -m py_compile \
  core/locale_store.py \
  core/locale_bundle.py \
  core/locale_handoff.py \
  core/locale_quality.py \
  core/locale_executor.py \
  core/locale_runtime.py \
  ui/localization.py
```

Expected: no output.

- [ ] **Step 4: Perform a manual smoke check in the app**

Verify:
- a successful Korean origin publication creates locale translation queue rows
- `en-US` runtime can produce a draft and publishable artifact
- a failed `ja-JP` quality gate records an incident without changing Korean canon
- deferred locale publish queue rows are created but no foreign upload runs yet

- [ ] **Step 5: Commit the finished implementation**

```bash
git add core/locale_store.py core/locale_bundle.py core/locale_handoff.py \
  core/locale_quality.py core/locale_executor.py core/locale_runtime.py \
  ui/localization.py ui/app.py tests/test_locale_store.py tests/test_locale_bundle.py \
  tests/test_locale_handoff.py tests/test_locale_quality.py tests/test_locale_executor.py \
  tests/test_locale_runtime.py tests/test_localization_ui.py tests/test_ui_helpers.py
git commit -m "feat: add locale pipeline foundation"
```

## Deferred Follow-Up Plans

Do not expand this plan in place. Create separate plans later for:

- concrete overseas platform client interfaces and adapters
- locale-specific marketing generation
- locale publish queue execution against real external sites
- locale credential storage if a platform requires separate accounts

This keeps the locale pipeline foundation independently buildable and prevents unknown external sites from bloating the first implementation.
