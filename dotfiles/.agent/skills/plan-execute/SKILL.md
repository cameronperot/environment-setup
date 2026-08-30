---
name: plan-execute
description: Executes an implementation plan document phase by phase, with per-task verification and a hard gate before each next phase. Use only when explicitly asked to execute or implement a plan or design document. Do not invoke proactively after writing or reviewing a plan.
---

# Execute Plan

Execute an implementation plan document one phase at a time. Later phases assume earlier ones are complete and verified, so a phase is finished only when every one of its tasks is done and its verification passes — never build on unverified ground.

Trailing input after `/skill:plan-execute` is the path to the plan file, followed by any additional constraints on execution; with no input, ask which plan to execute.

## Workflow

1. **Reconnaissance and uncertainty check**:
   - Read the plan file in full before doing any work. Note the goal, phases, tasks, verification steps, stated dependencies, and flagged uncertainties.
   - If there are unresolved uncertainties, ambiguities, or missing prerequisites in the plan, flag them and ask the user to resolve them before execution starts.
   - Verify the starting state matches the plan's assumptions: correct branch/commit, clean tree (or an intentionally dirty one the plan accounts for), and if the plan records a baseline, re-run it — if it no longer holds, stop and report before executing anything.
2. **Map structure**:
   - Explicit phases or milestones are the execution units. If the plan has no explicit phases, treat each top-level section containing tasks as a phase; if it has no structure at all, treat the entire plan as a single phase.
3. **Track progress**:
   - Build a todo list covering every task of every phase in plan order. The todo list is the live, session-visible status; it is not persisted — the plan file is.
   - If the plan file uses checkboxes, they are the source of truth for progress: resume from the first unchecked task, and spot-check that already-checked work actually exists before trusting it.
   - Mirror progress in the todo list: mark each task in progress before starting it, and mark it complete immediately after its verification passes.
   - At each phase gate, also update the plan file's checkboxes (step 5) so the persisted record stays in sync with the todo list.
4. **Execute current phase**:
   - Read the context a task needs before starting it, and finish each task fully before starting the next.
   - Complete tasks in plan order unless the plan specifies a different dependency order or marks tasks as order-independent; in the latter case any order is acceptable, but a task is still only started after its stated dependencies are done.
   - When fixing a bug, first write a test that reproduces it and fails if possible/feasible, then implement the fix.
   - Verify each task as the plan specifies; when the plan gives no verification step, run the narrowest check that would catch a mistake (affected tests, a build command, or executing changed code).
   - Verify each task's output before the next task depends on it. Work is done or working only after its test, command, or query has actually run and output is inspected.
   - Show the evidence: include the command and the part of its output that proves the claim; never assert success from reading code alone.
   - Make checks pass honestly: never delete, skip, weaken, or special-case a test to get a green result. If a test is genuinely wrong, explain why and ask before changing it.
   - Fix a failing check before starting the next task. Do not defer a red check or note it "to fix later".
   - Distinguish declared intermediate states from failures: if the plan explicitly states a phase ends non-green and defines a substitute gate, verify the substitute gate as written — that red is expected, not a blocker. Any red the plan did not declare is still a hard stop.
5. **Phase gate**:
   - Re-read the phase's section in the plan and compare each task against what was actually done.
   - Confirm every task in the phase is complete and every verification passes with evidence. "Mostly done", skipped, or deferred means the phase is not complete.
   - Mark the phase's tasks complete in the plan file if it uses checkboxes.
   - Do not commit unless the plan or the user asked for commits; if per-phase commits were requested, commit the phase's code changes after its gate passes, and keep plan-file checkbox updates in a separate commit from code.
   - Only then begin the next phase. Never pull tasks from a later phase forward, even when editing the same file.
6. **Repeat steps 4–5** until every phase in the plan is complete.
7. **Completion and artifact sweep**:
   - Confirm every task across all phases is complete and the original goal is achieved.
   - Sweep related artifacts without being asked: check every surface that states or derives from what changed (notebook/doc markdown matching computed constants and runtimes, related documentation, configurations) and either update them or explicitly report "checked — no change needed". The sweep is part of the change, not a follow-up; report its outcome in the final summary.
   - Run the plan's overall verification or the project's full test suite and linter (e.g. `uv run pytest && uv run ruff check`).
   - Interpret the final gate relative to the plan's recorded baseline (or the one re-verified at start): the requirement is no new failures beyond the baseline. Where the baseline had failures, report the failure sets side by side (pre-existing vs. current) rather than a bare pass/fail.
   - Report completion covering: what changed (which files), how it was verified (command and proving output evidence), the artifact sweep outcome, any deviations from the plan, and any follow-ups. State plainly what could not be verified, and why.

## Handling blockers and deviations

- **Mechanical mismatch** (a renamed file or symbol, an obvious typo in the plan): adapt, continue, and record the deviation for the final report.
- **Blocked**: document the blocker, attempt alternatives, and ask for guidance if still stuck.
- **Looping**: if the same check has failed after three genuinely different fix attempts, stop and report — what was tried, why each attempt failed, and the current diagnosis. Do not attempt a fourth variation; escalating is not failure, it is the correct outcome for a check you cannot make pass.
- **Scope changed**: pause, present the reassessment to the user, and update the plan only with their approval before continuing; record the change in the final report.
- **Plan is flawed**: stop, explain the issue clearly, and propose adjustments before proceeding. Do not improvise a new design mid-execution.
- **Integrity**: never mark a task complete that is not, and never report unverified work as verified.
