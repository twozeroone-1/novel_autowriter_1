# Handoff

Single shared coordination file for humans and models.

## Read First

- Read this file before starting work.
- Update this file when you finish meaningful work.
- If supporting artifacts are needed, place them under `artifacts/` and reference them here.

## Project State

- Project: `novel_autowriter_1`
- Collaboration style: repository-file-based indirect collaboration
- Latest known main commit: `66a670c`
- Data policy: runtime project data lives under `data/` and is not tracked by Git

## Current Task

- No active task recorded

## Done

- Hardened JSON/data loading in `core/context.py`
- Changed LLM failure handling to explicit exceptions in `core/llm.py`
- Added safer filename generation in `core/generator.py`
- Added safer session/project handling in `main.py`
- Untracked `data/` from Git and updated docs
- Simplified collaboration structure to one shared `handoff.md`

## Next

- Add lightweight tests for `ContextManager` load/normalize behavior
- Add lightweight tests for filename sanitization and collision handling
- Add a small documented validation flow for local checks

## Blocked

- None recorded

## Durable Notes

- Collaboration memory lives in repository files, not in tool-specific hidden session state.
- Antigravity internal files under `.gemini/antigravity/...` can be referenced, but they are not the source of truth.
- Runtime novel/project data under `data/` should remain outside Git tracking.
- LLM failures should surface as explicit errors, not be stored as generated content.

## Changed Files

- `main.py`
- `core/context.py`
- `core/generator.py`
- `core/llm.py`
- `core/automator.py`
- `.gitignore`
- `README.md`

## Update Template

Use this shape when updating:

- Current Task:
- Done:
- Next:
- Blocked:
- Durable Notes:
- Changed Files:
