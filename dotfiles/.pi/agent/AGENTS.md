# Global Agent Notes
## Environment

You run inside a container — don't assume it mirrors the host machine. Work only within the current working directory unless instructed otherwise; if something you expect (a tool, a path, a setting) is missing, say so instead of hunting for it elsewhere.

## Extension Tools

Beyond the built-ins, three tools are registered and active by default:

- `todo` — track multi-step work as a checklist; keep it current as steps complete.
- `questionnaire` — ask the user structured questions. Use it instead of guessing when requirements are ambiguous.
- `subagent` — delegate a task to a child agent with its own context window; only its final output returns here.

## Subagent Roles

- `scout` — read-only codebase recon; maps relevant files, entry points, data flow, and risks before implementing or planning.
- `docs-researcher` — read-only research on external libraries, APIs, and specs; returns a sourced, version-aware brief.
- `planner` — read-only; turns requirements plus scout findings into a minimal, numbered, verifiable implementation plan.
- `engineer` — implements a concrete plan or task: writes/edits code, runs tests; write-capable implementation agent (cheap model, max thinking effort).
- `test-runner` — runs the project's existing tests/build and returns a structured pass/fail triage; never edits source.
- `debugger` — diagnoses and fixes one specific bug (reproduce → isolate → fix → verify); edits files but does not implement features.
- `reviewer` — independent severity-ranked code review of a diff/change for correctness, security, and maintainability.
- `security-auditor` — read-only security audit of specified code/diff; reachable vulnerabilities with attack scenarios and remediation.
- `pr-summarizer` — generates a PR/commit title and summary from the current git diff.

Children cannot see this conversation and cannot delegate further — make each task well-defined and self-contained.
