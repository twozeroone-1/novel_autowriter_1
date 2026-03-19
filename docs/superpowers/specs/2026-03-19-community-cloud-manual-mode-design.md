# Community Cloud Manual Mode Design

**Goal**

Deploy this Streamlit app to Streamlit Community Cloud as a low-frequency personal tool for manual and semi-automatic writing workflows, while disabling background automation and external platform upload paths that do not fit the hosting model.

**Background**

The current app assumes a local workstation runtime:

- project data is stored under `data/projects`
- API keys can be stored in `.env` or `keyring`
- background automation services start at app boot
- UI exposes local filesystem paths and folder-opening actions
- external platform upload uses credentials and scheduled/background execution

Those assumptions conflict with Streamlit Community Cloud. Community Cloud is free and suitable for intermittent interactive use, but app instances are not a durable replacement for a personal workstation. The deployment must therefore narrow scope to the workflows that still make sense:

- project setup
- idea and plot work
- chapter generation
- review
- semi-automatic state/summary approval

## Approaches

### Option 1: Deploy the app unchanged

Keep the current codebase and deploy directly.

Pros:
- fastest initial deployment
- no architectural work

Cons:
- project files remain tied to local server disk
- background services may start in an unsuitable environment
- upload/automation UI suggests capabilities that will not reliably work
- `.env`, `keyring`, local-path, and folder-opening assumptions leak into cloud UX

### Option 2: Community Cloud runtime mode with remote file-backed storage

Add an explicit cloud runtime mode. Keep the existing local file model for local use, but swap to a remote file-backed storage backend in cloud mode and hide unsupported functionality.

Pros:
- preserves current project/data shape
- keeps local workflow intact
- makes Community Cloud usable for manual and semi-automatic work
- minimizes domain refactoring

Cons:
- requires introducing a storage abstraction
- remote saves are slower than local disk
- unsupported features must be explicitly hidden

### Option 3: Full hosted SaaS rewrite with database-backed persistence

Replace file-oriented storage with a first-class hosted database and redesign the app around multi-session cloud behavior.

Pros:
- best long-term hosted architecture
- stronger concurrency and persistence story

Cons:
- far beyond current scope
- expensive in time and complexity
- unnecessary for low-frequency single-user usage

## Recommendation

Choose Option 2.

The app already organizes most project data as JSON and Markdown files. That makes a remote file-backed backend the shortest path to a usable hosted version. The cloud deployment only needs to support interactive manual work; it does not need to preserve all workstation-era capabilities.

## Architecture

Introduce two explicit runtime concerns:

1. **Runtime mode**
- `local`
- `community_cloud`

2. **Storage backend**
- local filesystem backend
- GitHub repository backend

The existing code should continue to think in terms of project files such as:

- `config.json`
- `characters.json`
- chapter markdown files
- review report markdown files

Instead of reading and writing those files directly everywhere, the app will route project persistence through a storage interface. Local mode will use the filesystem implementation. Community Cloud mode will use the GitHub-backed implementation.

## Runtime behavior

### Local mode

Preserve existing behavior:

- `data/projects` remains the project root
- `.env` and `keyring` behavior remain available
- background services may start
- upload/automation tabs remain visible
- local path hints and folder-open actions remain available

### Community Cloud mode

Change behavior:

- disable background automation service startup
- disable publishing background service startup
- hide automation and upload tabs
- remove local path hints and folder-open buttons
- replace local-save UX with cloud-save wording
- prefer Streamlit secrets for credentials and API configuration
- disable `.env` writes, `keyring` writes, and Gemini CLI controls

## Persistence model

Use a GitHub private repository as the cloud persistence layer.

Each project remains file-based. A project can be represented as a directory tree rooted at a configured prefix, for example:

`projects/<project_name>/config.json`
`projects/<project_name>/characters.json`
`projects/<project_name>/chapters/<filename>.md`

This keeps the project format inspectable and close to the existing local model.

### Save semantics

- read latest file content from GitHub on demand
- write full file content back through the GitHub Contents API
- surface save failures to the user
- do not claim success if remote persistence fails

### Concurrency

This deployment targets a low-frequency single-user workflow. Strong multi-user conflict handling is out of scope. The implementation only needs a conservative failure mode:

- if a write is rejected because the remote file changed, show a reload/retry message

## UI changes

### Tabs

Keep:
- project settings
- generation
- review
- semi-auto mode

Hide:
- automation mode
- external platform upload

### Banner

Show one clear banner at the top:

`클라우드 버전은 수동/반자동 작업 전용입니다. 자동화 연재와 외부 플랫폼 업로드는 숨겨집니다.`

### Save and file actions

In Community Cloud mode:

- remove “저장 폴더 열기”
- remove raw local path displays
- keep explicit save buttons
- add download actions where file retrieval is useful
- show logical save messages instead of server filesystem paths

## Secrets and credentials

### Local mode

Keep current behavior:
- `.env`
- runtime env edits
- optional `keyring`
- optional Gemini CLI

### Community Cloud mode

Use secrets only:
- OpenAI/Gemini API keys from Streamlit secrets or environment
- GitHub token/repo settings from Streamlit secrets or environment

Hide or disable:
- `keyring` save/delete controls
- `.env` save controls
- Gemini CLI diagnostics and test actions

## Error handling

In Community Cloud mode:

- if required GitHub storage secrets are missing, fail fast with a clear configuration error
- if a remote read fails, show a user-facing load error instead of silently resetting project data
- if a remote save fails, keep the edited text in session and show a retryable error
- unsupported features should be hidden, not shown as broken

## Testing

Test at three levels:

1. runtime/config tests
- detect runtime mode correctly
- require GitHub storage settings in cloud mode

2. storage tests
- save/load config and characters through the remote backend contract
- save/load markdown documents through the same abstraction
- surface remote write failure cleanly

3. UI tests
- cloud mode hides automation/upload tabs
- cloud mode hides local filesystem affordances
- cloud mode prefers secrets-only API behavior where applicable
- local mode remains unchanged

## Scope exclusions

This change does not attempt to:

- make scheduled automation reliable on Community Cloud
- make platform upload reliable on Community Cloud
- redesign the app for multi-user collaboration
- migrate all existing local data automatically to GitHub
- replace the local file-based project model with a full database

## Success criteria

The work is successful when:

- the app can run locally with existing behavior unchanged
- the app can run on Community Cloud in a restricted manual/semi-auto mode
- project data persists through a configured GitHub repository in cloud mode
- unsupported automation/upload capabilities are not exposed in cloud mode
- the user can generate, review, save, reopen, and continue writing from the hosted app
