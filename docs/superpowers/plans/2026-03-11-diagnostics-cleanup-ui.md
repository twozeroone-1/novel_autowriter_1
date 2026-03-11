# Diagnostics Cleanup UI Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep only the last 24 hours of diagnostics on disk and present the diagnostics panel as a Korean read-only viewer.

**Architecture:** Add a small retention cleanup path to `core.diagnostics` so append/load both normalize stored files to the 24-hour window. Keep the UI changes inside `ui.diagnostics` by translating labels and switching raw payload rendering from editable inputs to read-only code/text output.

**Tech Stack:** Python, unittest, Streamlit, Playwright smoke verification

---

### Task 1: Retention cleanup

**Files:**
- Modify: `core/diagnostics.py`
- Test: `tests/test_diagnostics.py`

- [ ] **Step 1: Write the failing retention cleanup test**
- [ ] **Step 2: Run the diagnostics tests to verify the new assertion fails**
- [ ] **Step 3: Implement minimal cleanup-on-write/load behavior**
- [ ] **Step 4: Run diagnostics tests again to verify they pass**

### Task 2: Diagnostics panel copy and read-only rendering

**Files:**
- Modify: `ui/diagnostics.py`
- Test: `tests/test_diagnostics_ui.py`

- [ ] **Step 1: Write failing UI helper assertions for Korean copy / read-only detail metadata**
- [ ] **Step 2: Run the UI helper tests to verify failure**
- [ ] **Step 3: Implement minimal label and detail rendering helpers**
- [ ] **Step 4: Run UI helper tests again to verify they pass**

### Task 3: Verification

**Files:**
- Verify only

- [ ] **Step 1: Run targeted `py_compile`**
- [ ] **Step 2: Run full `unittest discover -s tests -v`**
- [ ] **Step 3: Re-check the worktree UI in the browser**
