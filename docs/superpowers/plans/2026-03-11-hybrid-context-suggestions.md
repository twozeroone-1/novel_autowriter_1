# Hybrid Context Suggestions Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add consistent AI-generated `STATE` and `PREVIOUS SUMMARY` suggestions across interactive modes while enabling safe automatic context updates in unattended automation mode.

**Architecture:** Introduce a shared context-suggestion layer that can produce a state suggestion and a summary suggestion from a finalized chapter body. Interactive tabs render suggestions and save only on explicit user confirmation; automation uses the same suggestion path but auto-applies results with backup and runtime logging.

**Tech Stack:** Python, Streamlit, unittest, existing `Generator`, `Automator`, `ContextManager`, automation runtime/store

---

## File Map

- Modify: `core/generator.py`
  - Expose a shared way to produce `STATE` and `PREVIOUS SUMMARY` suggestions without forcing immediate persistence in every mode.
- Modify: `core/automator.py`
  - Return both suggestions in pipeline results.
- Modify: `core/context.py`
  - Add safe backup/apply helpers if needed for automation.
- Modify: `ui/workspace.py`
  - Add suggestion buttons for `STATE` and `PREVIOUS SUMMARY`.
- Modify: `ui/chapters.py`
  - Add review-mode suggestion/approval flow and semi-auto suggestion rendering.
- Modify: `ui/automation.py`
  - Add automation settings for auto-applying suggestions and surface last context-update result.
- Modify/Create: `tests/test_automator.py`
  - Cover suggestion generation and failure capture.
- Modify/Create: `tests/test_ui_helpers.py`
  - Cover suggestion default selection logic.
- Create: `tests/test_context_updates.py`
  - Cover backup/apply rules if new helper functions are added.

## Chunk 1: Shared Suggestion Model

### Task 1: Write failing tests for shared suggestion generation

**Files:**
- Modify: `tests/test_automator.py`
- Modify: `core/automator.py`
- Modify: `core/generator.py`

- [ ] **Step 1: Add a failing success-path test**

```python
def test_run_single_cycle_returns_state_and_summary_suggestions():
    ...
    assert result["new_state"] == "state text"
    assert result["new_summary"] == "summary text"
```

- [ ] **Step 2: Run the focused test**

Run: `python -m unittest tests.test_automator`
Expected: FAIL because `new_state` is missing or summary behavior does not match.

- [ ] **Step 3: Implement minimal shared suggestion path**

Add the smallest production change so `Automator.run_single_cycle()` returns both suggestion fields from finalized chapter content.

- [ ] **Step 4: Re-run the focused test**

Run: `python -m unittest tests.test_automator`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add core/automator.py core/generator.py tests/test_automator.py
git commit -m "feat: return context suggestions from automator"
```

### Task 2: Write failing tests for isolated suggestion failures

**Files:**
- Modify: `tests/test_automator.py`
- Modify: `core/automator.py`

- [ ] **Step 1: Add tests for `state_error` and `summary_error` isolation**

```python
def test_run_single_cycle_keeps_pipeline_success_when_state_suggestion_fails():
    ...

def test_run_single_cycle_keeps_pipeline_success_when_summary_suggestion_fails():
    ...
```

- [ ] **Step 2: Run the focused tests**

Run: `python -m unittest tests.test_automator`
Expected: FAIL.

- [ ] **Step 3: Implement minimal try/except separation**

Keep each suggestion block isolated so chapter generation/save still succeeds.

- [ ] **Step 4: Re-run the focused tests**

Run: `python -m unittest tests.test_automator`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add core/automator.py tests/test_automator.py
git commit -m "test: isolate context suggestion failures"
```

## Chunk 2: Interactive Mode Approval Flows

### Task 3: Add workspace suggestion actions

**Files:**
- Modify: `ui/workspace.py`
- Modify: `tests/test_ui_helpers.py`

- [ ] **Step 1: Add failing tests for summary/state suggestion helpers**

```python
def test_workspace_summary_suggestion_uses_generated_text():
    ...
```

- [ ] **Step 2: Run the focused UI helper tests**

Run: `python -m unittest tests.test_ui_helpers`
Expected: FAIL.

- [ ] **Step 3: Add minimal helper and button wiring**

Support:
- `STATE AI 초안 생성`
- `PREVIOUS SUMMARY 초안 생성`

- [ ] **Step 4: Re-run the focused tests**

Run: `python -m unittest tests.test_ui_helpers`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add ui/workspace.py tests/test_ui_helpers.py
git commit -m "feat: add workspace context suggestion actions"
```

### Task 4: Add review-tab post-revision suggestion flow

**Files:**
- Modify: `ui/chapters.py`
- Modify: `tests/test_ui_helpers.py`

- [ ] **Step 1: Add failing tests for review suggestion gating**

```python
def test_review_mode_only_shows_context_suggestions_after_revised_draft_exists():
    ...
```

- [ ] **Step 2: Run the focused tests**

Run: `python -m unittest tests.test_ui_helpers`
Expected: FAIL.

- [ ] **Step 3: Implement minimal post-revision suggestion UI**

Only after revised draft exists:
- show `STATE 제안 생성`
- show `PREVIOUS SUMMARY 제안 생성`
- save only when user confirms latest-state update

- [ ] **Step 4: Re-run the focused tests**

Run: `python -m unittest tests.test_ui_helpers`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add ui/chapters.py tests/test_ui_helpers.py
git commit -m "feat: add review-tab context suggestion approval"
```

### Task 5: Finish semi-auto review suggestions

**Files:**
- Modify: `ui/chapters.py`
- Modify: `tests/test_ui_helpers.py`
- Modify: `tests/test_automator.py`

- [ ] **Step 1: Extend the existing semi-auto tests to cover both suggestion panes**

```python
def test_semi_auto_review_prefills_state_from_ai_suggestion():
    ...
```

- [ ] **Step 2: Run the focused tests**

Run: `python -m unittest tests.test_ui_helpers tests.test_automator`
Expected: FAIL before UI wiring is complete.

- [ ] **Step 3: Implement minimal REVIEW rendering changes**

Show:
- `AI 제안 STATE`
- `AI 제안 PREVIOUS SUMMARY`

Use editable fields for final save values only.

- [ ] **Step 4: Re-run the focused tests**

Run: `python -m unittest tests.test_ui_helpers tests.test_automator`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add ui/chapters.py tests/test_ui_helpers.py tests/test_automator.py
git commit -m "feat: add semi-auto context suggestions"
```

## Chunk 3: Automation Auto-Apply with Backup

### Task 6: Add failing tests for automation backup/apply rules

**Files:**
- Create: `tests/test_context_updates.py`
- Modify: `core/context.py`
- Modify: `ui/automation.py`

- [ ] **Step 1: Write a failing test for backup-before-apply**

```python
def test_apply_context_update_backs_up_previous_state_and_summary():
    ...
```

- [ ] **Step 2: Write a failing test for partial failure preservation**

```python
def test_apply_context_update_keeps_previous_summary_on_failure():
    ...
```

- [ ] **Step 3: Run the focused tests**

Run: `python -m unittest tests.test_context_updates`
Expected: FAIL.

- [ ] **Step 4: Implement minimal backup/apply helpers**

Add helper(s) that:
- load current config
- snapshot previous values
- write updated values conditionally
- return a structured result for logging

- [ ] **Step 5: Re-run the focused tests**

Run: `python -m unittest tests.test_context_updates`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add core/context.py ui/automation.py tests/test_context_updates.py
git commit -m "feat: add automation context backup and apply helpers"
```

### Task 7: Surface automation options and runtime outcome

**Files:**
- Modify: `ui/automation.py`
- Modify: automation runtime/store files as needed after inspection
- Modify: related tests for automation UI/runtime

- [ ] **Step 1: Add failing tests for configuration defaults and formatting**

```python
def test_automation_context_update_defaults_to_enabled():
    ...
```

- [ ] **Step 2: Run focused automation tests**

Run: `python -m unittest tests.test_automation_ui tests.test_automation_runtime`
Expected: FAIL.

- [ ] **Step 3: Implement minimal UI and runtime plumbing**

Expose:
- `회차 완료 후 STATE 자동 갱신`
- `회차 완료 후 PREVIOUS SUMMARY 자동 갱신`

Persist configuration and show last outcome summary.

- [ ] **Step 4: Re-run focused automation tests**

Run: `python -m unittest tests.test_automation_ui tests.test_automation_runtime`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add ui/automation.py tests/test_automation_ui.py tests/test_automation_runtime.py
git commit -m "feat: add automation context update controls"
```

## Chunk 4: Final Verification

### Task 8: Run regression verification

**Files:**
- No new files unless regressions appear

- [ ] **Step 1: Run the full relevant test set**

Run: `python -m unittest tests.test_automator tests.test_ui_helpers tests.test_context_manager tests.test_context_updates tests.test_automation_ui tests.test_automation_runtime`
Expected: PASS.

- [ ] **Step 2: Run a lightweight manual smoke test**

Run: `streamlit run ui/app.py`
Expected:
- workspace shows suggestion actions
- review tab only offers context update after revised draft exists
- semi-auto review shows both suggestions
- automation shows auto-update settings and preserves failures safely

- [ ] **Step 3: Commit**

```bash
git add .
git commit -m "feat: add hybrid context suggestions across modes"
```

Plan complete and saved to `docs/superpowers/plans/2026-03-11-hybrid-context-suggestions.md`. Ready to execute?
