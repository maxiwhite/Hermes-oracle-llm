# Hermes Continuous Executor Design

Date: 2026-09-23
Status: approved operating direction; written design pending final review
Baseline: `ff68507`, 78 tests passing

## Outcome

Hermes continuously selects and completes valuable local work without waiting for Maxi on routine decisions. Approval gates apply to consequential effects, not ordinary engineering choices. If one action is gated, Hermes queues it and continues another mission.

## Non-negotiable boundaries

- Every registered project keeps its own repository, branch, data, tests, and evidence.
- Fridge Brain remains the leading dependency unless current evidence changes the ranking.
- Local models and deterministic tools are the default.
- No push, merge, deployment, publishing, paid API, external message, permission change, credential operation, or destructive action without explicit approval.
- Failed work never damages the last healthy checkpoint.

## Architecture

The existing employee loop remains the scheduler. A new executor layer converts an eligible task into a typed action plan and runs only allowlisted operations. Free-form model text never becomes a shell command.

Each mission runs in an isolated git worktree created from a verified base commit. The primary checkout remains untouched. Hermes records the base commit, repository identity, commands, exit codes, changed files, test results, and final disposition.

## Task and action model

A task contains: project ID, repository root, objective, priority, dependencies, action kind, acceptance checks, risk effects, and status.

Initial allowlisted action kinds:

1. `inspect_repo` — status, branch, recent commits, configured tests.
2. `verify` — run a repository-defined test, lint, typecheck, or build command.
3. `apply_patch` — apply an explicit bounded patch inside the mission worktree.
4. `checkpoint` — create a local commit only after acceptance checks pass.
5. `report` — write an evidence receipt and update mission status.

Commands use argument arrays, fixed timeouts, captured output, and repository-local working directories. Shell metacharacters and paths outside the registered mission worktree are rejected.

## Autonomy policy

Automatically allowed: inspect local files; choose and sequence safe missions; create isolated branches/worktrees; edit files inside the worktree; run local tests/builds/linters; revert failed mission worktrees; create local commits; update evidence and rankings.

Approval required: network writes; pushes; merges; releases; deployment; publishing; money or paid inference; external messaging; credentials and permissions; deleting valuable data; modifying another project's repository; changing this policy.

Approval is attached to one proposed effect. A pending approval changes that task to `awaiting_approval`; it does not stop the worker.

## Execution state machine

`queued → selected → preflight → working → verifying → checkpointed → complete`

Alternative exits: `awaiting_approval`, `blocked`, or `failed_recoverable`. On failure, Hermes records evidence, removes only the disposable mission worktree when safe, and selects another task.

## Health and recovery

The Windows task keeps the scheduler alive, permits battery operation, starts at logon, and restarts after crashes. A heartbeat proves liveness. A lock prevents duplicate workers. Idle cycles use negligible resources and do not call a model.

Before mutation Hermes verifies: registered repository, expected base, clean isolated worktree, sufficient disk space, no unresolved merge, and an available verification command. Checkpoint creation requires all acceptance checks to pass.

## Evidence

Every attempt emits a JSON receipt with timestamps, task and project IDs, base and result commits, commands, exit codes, changed files, verification summary, approval state, and recommended next action. Status reports must derive from receipts rather than model claims.

## Delivery sequence

1. Add typed task/effect contracts and effect-based approval classification.
2. Add deterministic allowlisted runner and repository boundary validation.
3. Add worktree lifecycle and recovery.
4. Connect the scheduler so pending approval never blocks unrelated work.
5. Add evidence receipts and health/status output.
6. Add one real low-risk verification mission for Hermes itself.
7. Run focused tests, then the complete suite.
8. Activate the upgraded Windows worker; do not push or deploy.

## Acceptance criteria

- Routine local tasks progress without human input.
- A gated task is queued while another safe task runs.
- Commands cannot escape the registered worktree.
- Failed verification creates no checkpoint.
- Successful verification creates a recoverable local commit and receipt.
- Restarting the worker resumes safely without duplicate execution.
- Existing 78-test behavior remains green, with new tests covering every executor boundary.
