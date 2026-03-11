# LLM Diagnostics Viewer Design

**Date:** 2026-03-11

## Goal

Add a diagnostics-only LLM run viewer for this Streamlit app so the user can inspect recent Gemini API and Gemini CLI activity when something goes wrong.

The feature must:

- record both successful and failed LLM requests
- keep full prompt and full response text
- work for `api`, `cli`, and `auto` backend modes
- keep only the most recent 24 hours of records
- stay out of the primary writing workflow unless the user explicitly opens it

## Scope

### In scope

- project-scoped diagnostic logging for all LLM-backed features
- storage of run metadata plus raw prompt and response text
- UI summary in the sidebar
- hidden detailed viewer in `[1] 프로젝트 통합 설정`
- automatic cleanup of records older than 24 hours
- tests for write/read/filter/cleanup behavior

### Out of scope

- a new top-level `[7]` tab
- log export or download
- search across all historical runs
- sending stored logs back into any model
- long-term retention settings

## Current Context

- LLM calls currently enter through `core/llm.py`.
- Backend routing already exists through `core/llm_backend.py` with `auto`, `api`, and `cli`.
- The main diagnostic surface that already contains backend controls is the sidebar section rendered by `ui/workspace.py`.
- `[1] 프로젝트 통합 설정` is the best existing place for advanced, project-level tools that should stay out of the normal chapter-writing flow.
- The user explicitly wants this screen to be diagnostic-only, not part of the everyday author workflow.

## Recommended UX

### Placement

Keep the primary tabs unchanged as `[1]` through `[6]`.

Expose diagnostics in two layers:

1. Sidebar summary inside `API / 모델 설정`
2. Detailed viewer inside a collapsed `고급: 진단 / 실행 기록` expander at the bottom of `[1] 프로젝트 통합 설정`

This keeps the feature discoverable without making it a permanent top-level workflow surface.

### Sidebar summary

Show a compact 24-hour summary near the backend status area:

- run count in the last 24 hours
- failure count in the last 24 hours
- latest actual backend used
- button or cue to open the detailed viewer

The sidebar summary should never render raw prompt or response text.

### Detailed viewer

Inside `[1] 프로젝트 통합 설정`, add a collapsed advanced section named `고급: 진단 / 실행 기록`.

The viewer should show:

- a short warning that raw prompts and responses may contain sensitive text
- filters for success/failure, requested backend, actual backend, and model
- newest-first list of recent runs from the current project only
- one compact row per run with:
  - timestamp
  - feature name
  - success/failure
  - requested backend
  - actual backend
  - model
  - duration
- expandable raw details per run:
  - prompt text
  - response text
  - stderr text
  - error text
  - fallback note

The default view should emphasize summary rows. Raw text should only appear when the user expands a record.

## Data Model

Store one JSON object per line.

Suggested record shape:

```json
{
  "timestamp": "2026-03-11T14:20:00+09:00",
  "project": "my_project",
  "feature": "chapter_generate",
  "requested_backend": "auto",
  "actual_backend": "api",
  "fallback_note": "cli failed -> api",
  "model": "gemini-2.5-flash",
  "success": true,
  "duration_ms": 18342,
  "prompt_text": "...",
  "response_text": "...",
  "stderr_text": "",
  "error_text": ""
}
```

`feature` should identify the user-facing operation, for example:

- `idea`
- `plot`
- `chapter_generate`
- `review`
- `revise`
- `character_extract`
- `token_estimate`

## Storage Design

Use per-project JSONL files under the project directory.

Suggested path:

`data/projects/<project>/diagnostics/llm_runs/YYYY-MM-DD.jsonl`

Reasons:

- simple append-only writes
- easy manual inspection when needed
- no database dependency
- natural separation by project and date

## Retention Policy

Keep only records from the last 24 hours.

Cleanup should run in two places:

1. immediately before or after appending a new record
2. when loading records for the viewer

This avoids unbounded growth even if the viewer is never opened.

## Logging Flow

All LLM-backed operations should log through one shared path.

The logging wrapper should:

1. capture start time
2. execute the requested LLM call
3. capture success/failure, backend information, and raw text
4. append the JSONL record
5. return the original result or re-raise the original failure path as needed

For `auto` mode:

- `requested_backend` stays `auto`
- `actual_backend` records the backend that actually produced the final result
- `fallback_note` records the reason if `cli` failed and `api` succeeded

## Error Handling

Diagnostics must never become the reason a user-facing LLM call fails.

Rules:

- if log writing fails, keep the original feature result and surface the logging failure only as non-fatal diagnostics
- malformed or partially unreadable log lines should be skipped, not crash the viewer
- cleanup failure should not block the main writing flow
- raw text display should use plain text widgets, not markdown rendering

## Security and Privacy

The viewer intentionally stores full prompt and response text because the user requested full diagnostic fidelity.

Mitigations:

- keep retention short at 24 hours
- scope records per project
- default detailed text to collapsed
- show a clear warning in the viewer that raw text may contain sensitive information

This feature does not add token cost by itself because the stored text is only written to local files after the LLM call completes.

## Testing Strategy

### Unit tests

- append a success record
- append a failure record
- read records newest-first
- skip malformed JSONL lines
- delete records older than 24 hours
- keep project logs isolated
- preserve `requested_backend`, `actual_backend`, and `fallback_note`

### Integration-style tests

- verify `core/llm.py` logs successful API calls
- verify `core/llm.py` logs successful CLI calls
- verify `auto` mode logs CLI-to-API fallback correctly
- verify log-write failures do not replace the original LLM result

### UI tests

- sidebar summary renders only compact metadata
- detailed viewer appears only in the advanced section
- filters narrow the visible runs correctly
- raw prompt and response text appear only when a record is expanded

## File Impact

Likely files to modify:

- `core/llm.py`
- `core/llm_backend.py`
- `core/context.py` or a new diagnostics helper module under `core/`
- `ui/workspace.py`
- tests under `tests/`

Recommended new module:

- `core/diagnostics.py`

That module should own record schema, file paths, retention cleanup, append, and query helpers so UI code does not need to know JSONL details.

## Decision Summary

- Do not add a `[7]` top-level tab.
- Store full prompt and response text for both success and failure cases.
- Retain only the last 24 hours of records.
- Show only summary metadata in the sidebar.
- Put the full diagnostics viewer in a collapsed advanced section inside `[1] 프로젝트 통합 설정`.
