# README Senior-Friendly Guide Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite `README.md` so first-time Windows users can install and run the app easily, while keeping advanced instructions lower in the document.

**Architecture:** Keep a single `README.md`, but split it into two layers: a beginner-first quick-start at the top and an advanced/developer section below. Use the real launcher and setup files already present in the repo so the document matches the product as shipped.

**Tech Stack:** Markdown, Windows batch launcher, Python/Streamlit runtime, existing repo docs structure.

---

## Chunk 1: Capture the Documentation Shape

### Task 1: Replace the README outline with a beginner-first structure

**Files:**
- Modify: `README.md`
- Reference: `run_novel_autowriter.bat`
- Reference: `.env.example`

- [ ] **Step 1: Re-read the existing README and launcher files**

Run: `Get-Content README.md`, `Get-Content run_novel_autowriter.bat`, `Get-Content .env.example`
Expected: Confirm the current README is hard to read and that the shipped launcher and env template exist.

- [ ] **Step 2: Rewrite the top half for beginner users**

Write these sections in plain Korean:
- program summary
- first-time install
- easiest launch method
- what to do on first launch
- basic troubleshooting

- [ ] **Step 3: Keep advanced information in a separate lower section**

Add a lower section for:
- direct command-line launch
- virtual environment activation
- dependency install
- moving or backing up `data`
- Git-related notes

- [ ] **Step 4: Verify the beginner path mentions only real files and current features**

Check:
- `run_novel_autowriter.bat`
- `.env.example`
- Gemini CLI option
- API key option

- [ ] **Step 5: Commit**

```bash
git add README.md
git commit -m "Rewrite README for beginner Windows users"
```

## Chunk 2: Verify Readability and Formatting

### Task 2: Validate the rewritten README

**Files:**
- Modify: `README.md` if wording needs cleanup

- [ ] **Step 1: Read the finished README from top to bottom**

Run: `Get-Content README.md`
Expected: The top section reads like a simple checklist with short steps.

- [ ] **Step 2: Run a lightweight syntax check**

Run: `..\..\venv\Scripts\python.exe -c "from pathlib import Path; Path('README.md').read_text(encoding='utf-8'); print('readme ok')"`
Expected: `readme ok`

- [ ] **Step 3: Confirm advanced material stays below the beginner guide**

Check that the advanced section starts after the simple install/run/troubleshooting flow.

- [ ] **Step 4: Commit any final wording cleanup**

```bash
git add README.md
git commit -m "Polish README wording"
```
