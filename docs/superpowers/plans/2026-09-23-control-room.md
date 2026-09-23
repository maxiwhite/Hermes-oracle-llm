# Hermes Control Room Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local, auto-refreshing Control Room that makes active work, verified builds, approvals, and next missions immediately clear.

**Architecture:** A pure Python snapshot builder reads redacted runtime state and verified local git evidence. FastAPI exposes the snapshot and serves a dependency-free HTML/CSS/JavaScript working surface at `/control`.

**Tech Stack:** Python 3.11, FastAPI, pytest, HTML, CSS, browser JavaScript.

**Spec:** `docs/superpowers/specs/2026-09-23-control-room-design.md`

## Global Constraints

- Local-only at `127.0.0.1`; no deployment or paid services.
- Read-only first slice; no approval mutation.
- Never expose secrets, prompts, credentials, or unrestricted paths.
- Evidence receipts and existing commits are the only source of verified-build claims.
- Preserve project boundaries and the existing API behavior.
- Keep body text at least 16px and regular labels at least 14px.

## Review Focus

- Missing or malformed JSON produces an empty/stale section, not a server error.
- Heartbeats older than two worker intervals display as stale.
- A receipt referencing a nonexistent commit is not marked verified.
- Unknown project paths never reach the response.
- HTML remains usable at narrow mobile widths and with JavaScript refresh failures.

---
### Task 1: Snapshot builder

**Files:**
- Create: `control_room/snapshot.py`
- Create: `control_room/__init__.py`
- Test: `tests/test_control_room_snapshot.py`

**Interfaces:**
- Produces: `build_snapshot(paths: RuntimeStatePaths, registry: dict, now: datetime) -> dict`
- Produces sections: `needs_maxi`, `working_now`, `recent_builds`, `next_moves`, `projects`, and `generated_at`.

- [ ] **Step 1: Write failing tests**

Create fixtures for valid, missing, and malformed task, approval, heartbeat, worker, receipt, and project files. Assert urgent approvals sort first, stale heartbeats are marked, invalid commits remain unverified, unknown projects are excluded, and malformed files yield empty sections.

- [ ] **Step 2: Verify RED**

Run: `.venv\Scripts\python.exe -m pytest -q tests/test_control_room_snapshot.py`
Expected: FAIL because `control_room.snapshot` does not exist.

- [ ] **Step 3: Implement minimal snapshot builder**

Use safe JSON readers returning typed defaults, project-ID joins instead of raw paths, timezone-aware stale calculations, and an injected commit-existence function for deterministic tests. Return plain serializable dictionaries only.

- [ ] **Step 4: Verify GREEN and commit**

Run the focused test, then:
`git add control_room tests/test_control_room_snapshot.py && git commit -m "feat: build verified control room snapshot"`
### Task 2: Local API and static delivery

**Files:**
- Create: `backend/routes/control_room.py`
- Modify: `backend/main.py`
- Create: `backend/static/control/index.html`
- Test: `tests/test_control_room_api.py`

**Interfaces:**
- Consumes: `build_snapshot(...)`
- Produces: `GET /v1/control-room` JSON and `GET /control` HTML.

- [ ] **Step 1: Write failing API tests**

Use FastAPI TestClient with temporary runtime state. Assert the JSON schema, redaction/unknown-project exclusion, HTML content type, and that existing `/health` remains unchanged.

- [ ] **Step 2: Verify RED**

Run: `.venv\Scripts\python.exe -m pytest -q tests/test_control_room_api.py`
Expected: 404 for both new routes.

- [ ] **Step 3: Implement routes**

Mount explicit routes rather than a broad filesystem server. Return `FileResponse` only for the known dashboard file. Construct snapshots with the existing runtime-state resolver and registered project data.

- [ ] **Step 4: Verify GREEN and commit**

Run the focused tests, then:
`git add backend control_room tests/test_control_room_api.py && git commit -m "feat: serve local control room data"`
### Task 3: Operational working surface

**Files:**
- Modify: `backend/static/control/index.html`
- Test: `tests/test_control_room_ui.py`

**Interfaces:**
- Consumes: `GET /v1/control-room`.
- Produces: four ordered panels, project filter, evidence drawer, refresh/stale states.

- [ ] **Step 1: Write failing UI contract tests**

Parse the HTML and assert unique landmarks for Needs Maxi, Working now, Recent builds, and Next moves; a project selector; an evidence dialog; a five-second refresh declaration; mobile viewport metadata; and no remote scripts, fonts, or images.

- [ ] **Step 2: Verify RED**

Run: `.venv\Scripts\python.exe -m pytest -q tests/test_control_room_ui.py`
Expected: FAIL because the static page is not yet complete.

- [ ] **Step 3: Implement the page**

Use semantic HTML and inline local CSS/JS. Render escaped text with DOM `textContent`, never `innerHTML`. Put Needs Maxi first, amber only for decisions, quiet green for verified receipts, and expose evidence in an accessible dialog. Poll every 5000ms; retain the last good snapshot and label connection failure.

- [ ] **Step 4: Verify GREEN and commit**

Run the focused tests, then:
`git add backend/static/control/index.html tests/test_control_room_ui.py && git commit -m "feat: add Hermes control room interface"`
### Task 4: Launch, regression, and activation

**Files:**
- Modify: `scripts/operator.py`
- Modify: `OPERATOR.md`
- Modify: `.gitignore`
- Test: `tests/test_operator_launcher.py`

**Interfaces:**
- Produces: `python scripts/operator.py --control-room`, starting the local API and opening `http://127.0.0.1:8000/control`.
- Ignores: runtime `continuous-worker.log`.

- [ ] **Step 1: Write failing launcher test**

Inject process and browser callables. Assert the command starts the existing API on loopback, opens only the control URL after health succeeds, and does not start a cloud model.

- [ ] **Step 2: Verify RED**

Run: `.venv\Scripts\python.exe -m pytest -q tests/test_operator_launcher.py`
Expected: FAIL because `--control-room` is unknown.

- [ ] **Step 3: Implement launcher and documentation**

Add the mutually exclusive flag, bounded health wait, browser open, and clear failure output. Document start/stop behavior and the read-only first-slice boundary. Add only the worker log path to `.gitignore`.

- [ ] **Step 4: Full verification**

Run:
`.venv\Scripts\python.exe -m pytest -q tests/test_control_room_snapshot.py tests/test_control_room_api.py tests/test_control_room_ui.py tests/test_operator_launcher.py`
Then run:
`.venv\Scripts\python.exe -m pytest -q`
Expected: all existing 78 tests plus new tests pass.

- [ ] **Step 5: Activate locally and commit**

Start the Control Room, request `/health`, `/v1/control-room`, and `/control`, and verify HTTP 200. Commit only after all checks:
`git add scripts/operator.py OPERATOR.md .gitignore tests/test_operator_launcher.py && git commit -m "feat: launch Hermes control room"`
