# Automated Serialization Mode Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `[7] 자동화 연재 모드`를 추가해 프로젝트별 작업 큐와 예약 규칙에 따라 회차를 자동 실행하고, `STATE`/`PREVIOUS SUMMARY`까지 무인 갱신한다.

**Architecture:** 기존 [core/automator.py](/c:/Users/W/novel_autowriter_1/core/automator.py)를 실행 엔진으로 재사용하고, 그 위에 `automation storage + schedule evaluator + runtime runner + new UI tab`를 얹는다. Streamlit 서버 프로세스가 살아 있는 동안 주기적으로 예약 도래 여부를 검사하고, 큐의 다음 작업을 하나씩 처리한다.

**Tech Stack:** Python, Streamlit, JSON/JSONL storage, unittest, Playwright

---

## File Structure

### New files

- `core/automation_store.py`
  - 프로젝트별 자동화 설정/큐/런타임/이력 저장
- `core/automation_scheduler.py`
  - daily/weekly/interval 스케줄 판정
- `core/automation_runtime.py`
  - 예약 실행 가능 여부 확인, 큐 소비, retry/paused 처리
- `ui/automation.py`
  - `[7] 자동화 연재 모드` UI
- `tests/test_automation_store.py`
  - 저장소 테스트
- `tests/test_automation_scheduler.py`
  - 스케줄 판정 테스트
- `tests/test_automation_runtime.py`
  - 런타임 상태 전이 테스트
- `tests/test_automation_ui.py`
  - UI 헬퍼 테스트

### Modified files

- `ui/app.py`
  - `[7]` 탭 추가 및 `ui.automation` 연결
- `ui/workspace.py`
  - 필요 시 사이드바에 자동화 상태 요약 1줄 추가
- `core/automator.py`
  - 런타임 결과 메타데이터 보강이 필요하면 최소 수정
- `tests/test_automator.py`
  - 자동화 런타임과 맞닿는 결과 필드 테스트 보강

---

## Chunk 1: Storage and Schedule Rules

### Task 1: Add failing tests for automation storage defaults

**Files:**
- Create: `tests/test_automation_store.py`
- Create: `core/automation_store.py`
- Test: `tests/test_automation_store.py`

- [ ] **Step 1: Write the failing test**

```python
def test_load_automation_config_returns_defaults_when_missing():
    store = AutomationStore(project_name="sample")
    config = store.load_config()
    assert config["enabled"] is False
    assert config["schedule"]["type"] == "daily"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `venv\Scripts\python.exe -m unittest tests.test_automation_store -v`
Expected: FAIL because `core.automation_store` does not exist yet

- [ ] **Step 3: Write minimal implementation**

Add `AutomationStore` with:

- project automation directory resolution
- default config payload
- `load_config()`
- `save_config()`

- [ ] **Step 4: Run test to verify it passes**

Run: `venv\Scripts\python.exe -m unittest tests.test_automation_store -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/automation_store.py tests/test_automation_store.py
git commit -m "Add automation storage defaults"
```

### Task 2: Add failing tests for queue storage and history append

**Files:**
- Modify: `tests/test_automation_store.py`
- Modify: `core/automation_store.py`
- Test: `tests/test_automation_store.py`

- [ ] **Step 1: Write the failing test**

```python
def test_save_and_load_queue_round_trips_jobs():
    store = AutomationStore(project_name="sample")
    jobs = [{"id": "job1", "title": "12화", "status": "pending"}]
    store.save_queue(jobs)
    assert store.load_queue()[0]["id"] == "job1"


def test_append_history_writes_jsonl():
    store = AutomationStore(project_name="sample")
    store.append_history({"job_id": "job1", "success": True})
    assert len(store.load_recent_history(limit=10)) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `venv\Scripts\python.exe -m unittest tests.test_automation_store -v`
Expected: FAIL because queue/history methods are missing

- [ ] **Step 3: Write minimal implementation**

Add:

- `load_queue()`, `save_queue()`
- `load_runtime()`, `save_runtime()`
- `append_history()`, `load_recent_history()`

- [ ] **Step 4: Run test to verify it passes**

Run: `venv\Scripts\python.exe -m unittest tests.test_automation_store -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/automation_store.py tests/test_automation_store.py
git commit -m "Add automation queue and history storage"
```

### Task 3: Add failing tests for schedule matching rules

**Files:**
- Create: `tests/test_automation_scheduler.py`
- Create: `core/automation_scheduler.py`
- Test: `tests/test_automation_scheduler.py`

- [ ] **Step 1: Write the failing test**

```python
def test_daily_schedule_matches_target_minute():
    now = datetime(2026, 3, 12, 21, 0, tzinfo=timezone.utc)
    rule = {"type": "daily", "time": "21:00"}
    assert is_schedule_due(rule, now=now, last_run_at=None) is True


def test_interval_schedule_uses_last_success_time():
    now = datetime(2026, 3, 12, 12, 0, tzinfo=timezone.utc)
    rule = {"type": "interval", "hours": 6}
    last_run_at = "2026-03-12T06:00:00+00:00"
    assert is_schedule_due(rule, now=now, last_run_at=last_run_at) is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `venv\Scripts\python.exe -m unittest tests.test_automation_scheduler -v`
Expected: FAIL because scheduler module does not exist yet

- [ ] **Step 3: Write minimal implementation**

Add:

- `is_schedule_due()`
- helpers for `daily`, `weekly`, `interval`
- minute-level duplicate trigger guard

- [ ] **Step 4: Run test to verify it passes**

Run: `venv\Scripts\python.exe -m unittest tests.test_automation_scheduler -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/automation_scheduler.py tests/test_automation_scheduler.py
git commit -m "Add automation schedule evaluator"
```

---

## Chunk 2: Runtime Runner

### Task 4: Add failing tests for single-job runtime execution

**Files:**
- Create: `tests/test_automation_runtime.py`
- Create: `core/automation_runtime.py`
- Test: `tests/test_automation_runtime.py`

- [ ] **Step 1: Write the failing test**

```python
def test_runtime_executes_next_pending_job_and_marks_done():
    fake_automator = FakeAutomator(success=True)
    runtime = AutomationRuntime(store=store, automator=fake_automator)
    runtime.tick(now=now)
    assert store.load_queue()[0]["status"] == "done"
    assert store.load_runtime()["status"] == "idle"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `venv\Scripts\python.exe -m unittest tests.test_automation_runtime -v`
Expected: FAIL because runtime module does not exist yet

- [ ] **Step 3: Write minimal implementation**

Add:

- `AutomationRuntime.tick()`
- due check
- next pending job selection
- `running -> done -> idle` transition
- history append

- [ ] **Step 4: Run test to verify it passes**

Run: `venv\Scripts\python.exe -m unittest tests.test_automation_runtime -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/automation_runtime.py tests/test_automation_runtime.py
git commit -m "Add automation runtime runner"
```

### Task 5: Add failing tests for retry and paused behavior

**Files:**
- Modify: `tests/test_automation_runtime.py`
- Modify: `core/automation_runtime.py`
- Test: `tests/test_automation_runtime.py`

- [ ] **Step 1: Write the failing test**

```python
def test_runtime_retries_once_then_pauses_queue_on_second_failure():
    fake_automator = FakeAutomator(success=False)
    runtime = AutomationRuntime(store=store, automator=fake_automator)
    runtime.tick(now=now)
    queue = store.load_queue()
    state = store.load_runtime()
    assert queue[0]["status"] == "failed"
    assert queue[0]["attempt_count"] == 2
    assert state["status"] == "paused"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `venv\Scripts\python.exe -m unittest tests.test_automation_runtime -v`
Expected: FAIL because retry/pause policy is not implemented yet

- [ ] **Step 3: Write minimal implementation**

Add:

- immediate one-time retry
- failure reason capture
- `paused` runtime transition
- `resume()` helper

- [ ] **Step 4: Run test to verify it passes**

Run: `venv\Scripts\python.exe -m unittest tests.test_automation_runtime -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/automation_runtime.py tests/test_automation_runtime.py
git commit -m "Pause automation after retried failure"
```

### Task 6: Add failing tests for runtime recovery after restart

**Files:**
- Modify: `tests/test_automation_runtime.py`
- Modify: `core/automation_runtime.py`
- Test: `tests/test_automation_runtime.py`

- [ ] **Step 1: Write the failing test**

```python
def test_runtime_skips_execution_when_paused():
    store.save_runtime({"status": "paused", "last_error": "boom"})
    runtime.tick(now=now)
    assert fake_automator.call_count == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `venv\Scripts\python.exe -m unittest tests.test_automation_runtime -v`
Expected: FAIL because paused guard is missing

- [ ] **Step 3: Write minimal implementation**

Add paused/running guards and runtime normalization on startup.

- [ ] **Step 4: Run test to verify it passes**

Run: `venv\Scripts\python.exe -m unittest tests.test_automation_runtime -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/automation_runtime.py tests/test_automation_runtime.py
git commit -m "Harden automation runtime recovery guards"
```

---

## Chunk 3: UI

### Task 7: Add failing tests for automation tab helper formatting

**Files:**
- Create: `tests/test_automation_ui.py`
- Create: `ui/automation.py`
- Test: `tests/test_automation_ui.py`

- [ ] **Step 1: Write the failing test**

```python
def test_format_runtime_status_maps_to_korean_labels():
    assert format_runtime_status("idle") == "대기"
    assert format_runtime_status("running") == "실행 중"
    assert format_runtime_status("paused") == "중지됨"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `venv\Scripts\python.exe -m unittest tests.test_automation_ui -v`
Expected: FAIL because `ui.automation` does not exist yet

- [ ] **Step 3: Write minimal implementation**

Create helpers for:

- runtime status labels
- schedule summary labels
- queue row labels

- [ ] **Step 4: Run test to verify it passes**

Run: `venv\Scripts\python.exe -m unittest tests.test_automation_ui -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add ui/automation.py tests/test_automation_ui.py
git commit -m "Add automation UI helpers"
```

### Task 8: Add the `[7] 자동화 연재 모드` tab and minimal wiring

**Files:**
- Modify: `ui/app.py`
- Modify: `ui/automation.py`
- Test: `tests/test_automation_ui.py`

- [ ] **Step 1: Write the failing test**

```python
def test_build_automation_tab_sections_returns_four_panels():
    sections = build_automation_sections(...)
    assert [section["key"] for section in sections] == [
        "schedule",
        "queue",
        "runtime",
        "history",
    ]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `venv\Scripts\python.exe -m unittest tests.test_automation_ui -v`
Expected: FAIL because tab helper is missing

- [ ] **Step 3: Write minimal implementation**

Add:

- `[7] 자동화 연재 모드` tab in `ui/app.py`
- `render_automation_tab(app)` in `ui/automation.py`
- schedule form, queue form, runtime panel, history panel

- [ ] **Step 4: Run test to verify it passes**

Run: `venv\Scripts\python.exe -m unittest tests.test_automation_ui -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add ui/app.py ui/automation.py tests/test_automation_ui.py
git commit -m "Add automated serialization tab"
```

### Task 9: Connect runtime polling to the app lifecycle

**Files:**
- Modify: `ui/app.py`
- Modify: `ui/automation.py`
- Modify: `core/automation_runtime.py`
- Test: `tests/test_automation_runtime.py`

- [ ] **Step 1: Write the failing test**

```python
def test_tick_respects_poll_guard_and_does_not_double_run_same_minute():
    runtime.tick(now=now)
    runtime.tick(now=now)
    assert fake_automator.call_count == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `venv\Scripts\python.exe -m unittest tests.test_automation_runtime -v`
Expected: FAIL because poll guard is missing

- [ ] **Step 3: Write minimal implementation**

Add:

- cached runtime service per project
- poll interval guard
- call to `tick()` from app orchestration path

- [ ] **Step 4: Run test to verify it passes**

Run: `venv\Scripts\python.exe -m unittest tests.test_automation_runtime -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add ui/app.py ui/automation.py core/automation_runtime.py tests/test_automation_runtime.py
git commit -m "Wire automation polling into app runtime"
```

---

## Chunk 4: Verification

### Task 10: End-to-end verification

**Files:**
- Verify only

- [ ] **Step 1: Run targeted syntax checks**

Run:

```bash
venv\Scripts\python.exe -B -m py_compile core\automation_store.py core\automation_scheduler.py core\automation_runtime.py ui\automation.py ui\app.py
```

Expected: exit code 0

- [ ] **Step 2: Run full tests**

Run:

```bash
venv\Scripts\python.exe -m unittest discover -s tests -v
```

Expected: all tests pass

- [ ] **Step 3: Run manual Playwright smoke**

Check:

- `[7]` 탭에서 스케줄 저장 가능
- 큐에 작업 추가 가능
- due 조건에서 자동 실행 시작
- 실패 시 `paused` 표시
- 성공 시 history 증가

- [ ] **Step 4: Commit final integration**

```bash
git add core/automation_store.py core/automation_scheduler.py core/automation_runtime.py ui/automation.py ui/app.py tests/test_automation_store.py tests/test_automation_scheduler.py tests/test_automation_runtime.py tests/test_automation_ui.py
git commit -m "Add scheduled automated serialization mode"
```
