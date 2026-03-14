# Plot Flow Expansion Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 저장된 대형 플롯을 검수, 반자동, 자동화 경로에도 선택적으로 반영한다.

**Architecture:** 기존 생성 경로의 플롯 옵션을 Reviewer와 Automator로 확장하고, 자동화는 프로젝트 단위 설정으로 저장해 런타임에서 재사용한다. UI는 각 탭에 동일한 토글 패턴을 유지해 사용자가 어느 경로에서든 같은 개념으로 플롯 반영을 제어할 수 있게 한다.

**Tech Stack:** Python, Streamlit, unittest

---

### Task 1: Add failing tests for plot propagation

**Files:**
- Modify: `tests/test_reviewer.py`
- Modify: `tests/test_automator.py`
- Modify: `tests/test_automation_runtime.py`
- Modify: `tests/test_automation_store.py`

- [ ] **Step 1: Write failing tests for reviewer plot context**
- [ ] **Step 2: Write failing tests for automator plot propagation**
- [ ] **Step 3: Write failing tests for automation config/runtime plot propagation**
- [ ] **Step 4: Run targeted tests and confirm failures**

### Task 2: Implement reviewer plot support

**Files:**
- Modify: `core/reviewer.py`

- [ ] **Step 1: Add optional plot arguments to review and revise methods**
- [ ] **Step 2: Include plot block only when enabled and stored plot exists**
- [ ] **Step 3: Run reviewer tests and confirm pass**

### Task 3: Implement semi-auto and automation plot support

**Files:**
- Modify: `core/automator.py`
- Modify: `core/automation_runtime.py`
- Modify: `core/automation_store.py`

- [ ] **Step 1: Extend automator signature with plot options**
- [ ] **Step 2: Read automation generation options and pass them to automator**
- [ ] **Step 3: Ensure automation config loads nested defaults safely**
- [ ] **Step 4: Run automator/runtime/store tests and confirm pass**

### Task 4: Implement UI controls

**Files:**
- Modify: `ui/chapters.py`
- Modify: `ui/automation.py`
- Modify: `ui/app.py`

- [ ] **Step 1: Add review tab plot controls and persist selected options**
- [ ] **Step 2: Add semi-auto plot controls and pass them into run_single_cycle**
- [ ] **Step 3: Add automation plot controls and save config values**
- [ ] **Step 4: Add any required session state keys**

### Task 5: Verify end-to-end behavior

**Files:**
- Modify: `tests/test_ui_helpers.py` if required by session state changes

- [ ] **Step 1: Run targeted tests for touched modules**
- [ ] **Step 2: Fix any regressions**
- [ ] **Step 3: Summarize behavior changes and residual risks**
