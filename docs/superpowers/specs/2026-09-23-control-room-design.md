# Hermes Control Room Design

Date: 2026-09-23
Status: approved direction
Audience: Maxi
Delivery: local-only; no public deployment

## Outcome

Create one calm, immediately readable space for seeing what Hermes and its workers are doing, what recently changed, what is blocked, and where Maxi must answer quickly. The interface replaces scattered logs and status messages with verified, actionable evidence.

## First viewport

The page opens directly on the working surface with four ordered areas:

1. **Needs Maxi** — consequential approvals, oldest/most urgent first, with one plain-language decision and its effect.
2. **Working now** — worker, project, mission, elapsed time, last heartbeat, and current state.
3. **Recent builds** — verified checkpoints with project, commit, changed files, tests, and result.
4. **Next moves** — ranked safe missions that will proceed automatically.

A narrow project switcher exposes the Top 8 while preserving repository boundaries. Fridge Brain remains visually marked as the leading dependency unless evidence changes its rank.

## Interaction

The default view contains no setup flow, marketing copy, or technical noise. Every card answers: what, where, verified by what, and what happens next. Selecting a card opens evidence details without leaving the board.

Approval controls are deliberately narrow: approve this effect, reject it, or defer it. Routine work never appears in Needs Maxi. A blocked approval does not pause unrelated work.

The board refreshes automatically every five seconds and clearly reports stale worker heartbeats. Empty, loading, and unavailable states explain the next useful action.

## Data and trust

A read-only snapshot service derives the board from Hermes runtime state, task and approval queues, worker heartbeats, evidence receipts, project registry, and local git metadata. The UI does not infer completion. A build appears verified only when a receipt records successful acceptance checks and the referenced local commit exists.

Secrets, full prompts, credentials, and unrestricted filesystem paths are never returned. Project identifiers are resolved through the registered project boundary.

## Technical shape

FastAPI serves a local JSON endpoint and a static single-page interface at `http://127.0.0.1:8000/control`. The first version uses plain HTML, CSS, and JavaScript to avoid a second build toolchain. The snapshot builder remains a tested Python module independent of the web layer.

The existing Windows worker and local API remain separate processes. The Control Room is read-only in its first slice; approval mutation is added only after effect-based approvals are implemented.

## Visual direction

Near-black precision workspace with restrained warm-white type, thin structural rules, and one amber signal reserved for items requiring Maxi. Verified work uses quiet green text rather than decorative status dots. Density is compact but readable, with 16px body text and strong keyboard focus.

Desktop uses a two-column operational grid; mobile becomes one ordered stream with Needs Maxi first. Motion is limited to subtle refresh and state transitions.

## Acceptance criteria

- Maxi can identify every urgent decision within five seconds.
- Current worker activity and stale heartbeats are distinguishable.
- Recent builds show only evidence-backed checkpoints.
- Project boundaries and Top 8 ranking are visible.
- The page works locally without cloud services or paid models.
- No secrets or unrestricted paths are exposed.
- Empty and malformed runtime files do not crash the page.
- Existing API and 78-test baseline remain green.
