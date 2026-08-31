---
name: plan-draft
description: Drafts structured, phased implementation plans with verifiable tasks, explicit dependencies, and artifact sweeps. Use only when explicitly asked to plan a change, draft an implementation plan, create a technical design, or break a task into phases. Do not use for executing or running existing plans (plan-execute).
---

# plan-draft

Draft succinct, phased implementation plans where every task has a verifiable success criterion and every phase gates on verified evidence.

Trailing input after `/skill:plan-draft` is the goal, scope, or target file path for the plan; with no input, derive the goal from conversation context or ask what change to plan.

## Principles

- **Succinct and action-focused**: Describe what to do, not how long it takes.
- **Omit large code blocks**: Include only critical signatures, type definitions, or configuration keys when necessary.
- **Verifiable goals**: Frame every task as a verifiable goal with an explicit success criterion, not a sequence of vague actions.
- **Strict phase gating**: Sequence work so each phase builds only on verified prior steps; never build on unverified ground.
- **Flag uncertainties early**: Identify assumptions, breaking changes, and trade-offs before drafting; ask the user to resolve open decisions before execution starts.
- **Built-in artifact sweep**: Every plan must conclude with an explicit sweep of related documentation, configs, and test suites.

## Workflow

1. Reconnaissance:
   - Do not read any other existing plans, specs, or design documents unless the user explicitly instructs you to; base the plan only on the user's stated goal and your own recon of the code.
   - Read relevant codebase files, types, and configurations to understand current architecture and patterns.
   - Inspect existing test suites and discover available test, lint, and build commands (e.g. `uv run pytest`).
   - Run the full test suite once to establish a baseline; record any pre-existing failures so phase gates are never confused with them.
   - Identify conventions in surrounding code to preserve style and architecture.
2. Resolve scope and uncertainties:
   - Define exact boundaries of what is in scope and what is explicitly out of scope.
   - List assumptions and identify any ambiguity that materially affects the design.
   - State the verified baseline (e.g. "suite green on <commit/ref>" or "3 pre-existing failures in <area>") in Key Decisions & Assumptions.
   - If multiple valid approaches exist, present trade-offs concisely and ask the user to decide before finalizing the plan.
   - List external dependencies and blockers outside the plan's control (access, credentials, upstream changes, third-party decisions); if any are unresolved, confirm with the user how to handle them before finalizing the plan.
3. Structure sequential phases:
   - Group work into logical, ordered phases where earlier phases provide stable foundations for later phases.
   - Define an explicit exit gate for each phase (the exact command or check proving the phase passed); a phase's entry condition is the prior phase's gate plus any declared non-sequential dependencies.
   - Make dependencies explicit in the plan itself: phases build on prior phase gates by default; call out any non-sequential or cross-phase dependencies (e.g. "Phase 3 also requires Phase 1's config key") rather than leaving them implicit.
   - Tasks within a phase execute in listed order by default; when several are independent of each other, say so (e.g. "Tasks 2–4 are order-independent") so parallel execution is safe.
   - Avoid creating too many phases for small tasks or a single monolithic phase for complex work.
   - End every phase at a verifiable state. By default that means the code compiles and tests pass; if a phase intentionally ends in an intermediate state (e.g. schema changed, consumers migrated in a later phase), the plan must say so explicitly and define a substitute gate (e.g. a scoped test subset, a dry-run command, or "new tests fail for the stated reason") so the gate never becomes a rubber stamp.
4. Define verifiable tasks:
   - Write tasks using markdown checkboxes (`- [ ]`) compatible with progress tracking.
   - Specify exact file paths to create, modify, or delete for each task.
   - State the narrowest, honest verification step for every task — usually an exact command, query, or automated test; where no command exists, describe the manual check concretely (what to run or open, and what result counts as passing) rather than inventing one.
   - For bug fixes, require writing a reproducing failing test before implementing the fix.
5. Add completion and artifact sweep:
   - Define a final phase to sweep all related surfaces without being asked.
   - Include verification that documentation, type annotations, and notebook markdown match the updated code.
   - Include running the full project test suite and linter as the final gate.
6. Present the plan:
   - Format the plan using the markdown structure below.
   - Write the plan to the markdown file expected by the invoking context (e.g. a requested path, or `specs/<plan-name>.md` in plannotator plan mode), updating it incrementally as understanding evolves rather than drafting it in one pass; only output the plan directly to the conversation when no file-based flow is active.

## Plan structure

```markdown
# Implementation Plan: <Feature or Task Title>

## Overview
<1–2 sentences explaining the goal, core approach, and scope boundaries.>

## Key Decisions & Assumptions
- <Decision or assumption with rationale>
- <Resolution of any ambiguities>

## Phase 1: <Phase Name>
- [ ] <Task 1: specific file path and exact change>
  - **Verification**: `<exact check command, test, or query>`
- [ ] <Task 2: specific file path and exact change>
  - **Verification**: `<exact check command, test, or query>`
- **Phase Gate**: `<exact command proving Phase 1 passes before starting Phase 2>`

## Phase 2: <Phase Name>
- [ ] <Task 1: specific file path and exact change>
  - **Verification**: `<exact check command, test, or query>`
- **Phase Gate**: `<exact command proving Phase 2 passes before starting Phase 3>`

## Phase N: Completion & Artifact Sweep
- [ ] Sweep related artifacts: update documentation, cross-references, and comments affected by changes
- [ ] Run full project verification suite
- **Final Gate**: `<full project test and lint command, e.g. uv run pytest && uv run ruff check>`
```

## Quality checklist

Before presenting a draft plan, verify:

- Every task is framed as an outcome with an explicit verification command, not vague prose like "investigate" or "update code".
- No verification step invents a command that does not actually check the outcome; manual checks are described concretely and used only when no command exists.
- No duration, time estimates, or sprint allocations are present; a brief complexity note (e.g. "Phase 2 is the large/risky one") is allowed and encouraged where size varies significantly between phases.
- Code blocks are omitted except for essential interfaces or schemas.
- Checkboxes (`- [ ]`) are used consistently for task tracking.
- The artifact sweep phase is included at the end.
- Dependencies between phases and tasks are stated in the plan; only non-obvious dependencies are annotated, so strictly linear plans stay clean.
