# Semi-Auto State Suggestion Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an AI-generated `CURRENT STATE` suggestion to the semi-automatic serialization review flow so users review and approve a proposed next-state instead of rewriting it manually.

**Architecture:** Extend the semi-auto pipeline result object to carry a `new_state` proposal and `state_error`, then update the review UI to display the AI proposal and seed the editable state textarea from that proposal. Preserve the current save boundary so config changes happen only after explicit user confirmation.

**Tech Stack:** Python, Streamlit, unittest, existing `Generator`/`Automator` pipeline

---

## File Map

- Modify: `core/automator.py`
  - Add state summarization to the single-cycle pipeline result.
- Modify: `ui/chapters.py`
  - Show AI-generated state suggestion in REVIEW mode and seed the final editable state field from it.
- Create or Modify: `tests/test_automator.py`
  - Verify `run_single_cycle()` returns `new_state` on success and `state_error` on failure.
- Modify: `tests/test_ui_helpers.py` or create a focused UI helper test file if extraction is needed
  - Verify the state-default selection logic.

## Chunk 1: Pipeline Result Extension

### Task 1: Add failing tests for automator state suggestion success

**Files:**
- Modify: `tests/test_automator.py`
- Modify: `core/automator.py`

- [ ] **Step 1: Inspect existing automator tests**

Run: `rg -n "Automator|run_single_cycle" tests`
Expected: find existing tests or confirm a new file is needed.

- [ ] **Step 2: Write a failing test for successful state suggestion**

```python
def test_run_single_cycle_includes_new_state_when_state_summary_succeeds():
    generator = FakeGenerator()
    reviewer = FakeReviewer()
    automator = Automator(project_name="sample", generator=generator, reviewer=reviewer)

    result = automator.run_single_cycle("Ep 5", "instruction", 2000)

    assert result["new_state"] == "updated state"
    assert "state_error" not in result
```

- [ ] **Step 3: Run the focused test**

Run: `python -m unittest tests.test_automator`
Expected: FAIL because `new_state` is not returned yet.

- [ ] **Step 4: Implement the minimal production change**

In `core/automator.py`, after summary update:

```python
try:
    result["new_state"] = self.generator.summarize_state(revised_draft)
except Exception as exc:
    result["state_error"] = str(exc)
```

- [ ] **Step 5: Run the focused test again**

Run: `python -m unittest tests.test_automator`
Expected: PASS for the new success-path assertion.

- [ ] **Step 6: Commit**

```bash
git add core/automator.py tests/test_automator.py
git commit -m "feat: add state suggestion to semi-auto pipeline"
```

### Task 2: Add failing tests for state suggestion failure fallback

**Files:**
- Modify: `tests/test_automator.py`
- Modify: `core/automator.py`

- [ ] **Step 1: Add a failing test for state-summary failure**

```python
def test_run_single_cycle_records_state_error_without_failing_pipeline():
    generator = FakeGenerator(state_error=RuntimeError("state boom"))
    reviewer = FakeReviewer()
    automator = Automator(project_name="sample", generator=generator, reviewer=reviewer)

    result = automator.run_single_cycle("Ep 5", "instruction", 2000)

    assert result["state_error"] == "state boom"
    assert "new_state" not in result
    assert "saved_path" in result
```

- [ ] **Step 2: Run the focused test**

Run: `python -m unittest tests.test_automator`
Expected: FAIL before fallback handling is correct.

- [ ] **Step 3: Keep failure isolated to the state suggestion block**

Ensure the `summarize_state()` call has its own `try/except` and does not affect previously completed outputs.

- [ ] **Step 4: Re-run the focused test**

Run: `python -m unittest tests.test_automator`
Expected: PASS and prior pipeline behavior still works.

- [ ] **Step 5: Commit**

```bash
git add core/automator.py tests/test_automator.py
git commit -m "test: cover state suggestion fallback in automator"
```

## Chunk 2: Review UI State Proposal

### Task 3: Extract and test the editable-state default selection logic

**Files:**
- Modify: `ui/chapters.py`
- Modify: `tests/test_ui_helpers.py`

- [ ] **Step 1: Add a small helper for review-state defaults**

Create a focused helper in `ui/chapters.py`, for example:

```python
def get_review_state_value(auto_result: Mapping[str, Any], current_config: Mapping[str, Any]) -> str:
    proposed = str(auto_result.get("new_state", "")).strip()
    if proposed:
        return proposed
    return str(current_config.get("state", ""))
```

- [ ] **Step 2: Write the failing tests**

```python
def test_get_review_state_value_prefers_new_state():
    value = module.get_review_state_value({"new_state": "fresh state"}, {"state": "old state"})
    assert value == "fresh state"

def test_get_review_state_value_falls_back_to_config_state():
    value = module.get_review_state_value({}, {"state": "old state"})
    assert value == "old state"
```

- [ ] **Step 3: Run the focused test file**

Run: `python -m unittest tests.test_ui_helpers`
Expected: FAIL before helper exists.

- [ ] **Step 4: Implement the helper minimally**

Add only the helper and wire no UI yet.

- [ ] **Step 5: Re-run the focused test file**

Run: `python -m unittest tests.test_ui_helpers`
Expected: PASS for the new helper tests.

- [ ] **Step 6: Commit**

```bash
git add ui/chapters.py tests/test_ui_helpers.py
git commit -m "test: add review state default helper"
```

### Task 4: Show AI state proposal and warning in the REVIEW screen

**Files:**
- Modify: `ui/chapters.py`
- Modify: `tests/test_ui_helpers.py`

- [ ] **Step 1: Add a failing test for warning conditions if practical**

If current test style supports it, add a helper for warning message conditions:

```python
def get_state_warning(auto_result: Mapping[str, Any]) -> str:
    ...
```

Then test:

```python
def test_get_state_warning_returns_message_when_state_error_exists():
    ...
```

If UI-only testing is too heavy, keep the helper-level test and skip direct Streamlit rendering assertions.

- [ ] **Step 2: Update REVIEW rendering**

In `ui/chapters.py`:
- read `result.get("new_state", "")`
- show a warning when `result.get("state_error")` exists
- show an expander or caption block for `AI 제안 STATE`
- set the editable `CURRENT STATE 업데이트` textarea value from `get_review_state_value(result, current_config)`

- [ ] **Step 3: Keep save behavior unchanged**

The save button must still write only the user-edited `new_state` textarea value and `new_summary` textarea value.

- [ ] **Step 4: Run the relevant tests**

Run: `python -m unittest tests.test_ui_helpers tests.test_automator`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add ui/chapters.py tests/test_ui_helpers.py tests/test_automator.py
git commit -m "feat: show AI state suggestion in semi-auto review"
```

## Chunk 3: Regression Verification

### Task 5: Verify end-to-end test coverage and no summary regressions

**Files:**
- Modify if needed: `tests/test_context_manager.py`
- Modify if needed: `tests/test_automator.py`
- Modify if needed: `tests/test_ui_helpers.py`

- [ ] **Step 1: Run the full relevant test set**

Run: `python -m unittest tests.test_automator tests.test_ui_helpers tests.test_context_manager`
Expected: all tests PASS.

- [ ] **Step 2: Run one broader smoke test around chapter UI helpers if fast enough**

Run: `python -m unittest tests.test_llm_parser tests.test_reviewer`
Expected: PASS with no regressions from new pipeline fields.

- [ ] **Step 3: Manually inspect the REVIEW step in Streamlit if desired**

Run: `streamlit run ui/app.py`
Expected:
- REVIEW step shows `AI 제안 STATE` when available
- warning appears when state generation fails
- editable state field is seeded from AI proposal
- save persists only reviewed values

- [ ] **Step 4: Commit**

```bash
git add core/automator.py ui/chapters.py tests/test_automator.py tests/test_ui_helpers.py
git commit -m "chore: verify semi-auto state suggestion flow"
```

Plan complete and saved to `docs/superpowers/plans/2026-03-11-semi-auto-state-suggestion.md`. Ready to execute?
