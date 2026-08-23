# Global Agent Notes
## Extension Tools

Beyond the built-ins, three tools are registered and active by default:

- `todo` — track multi-step work as a checklist; keep it current as steps complete.
- `questionnaire` — ask the user structured questions. Use it instead of guessing when requirements are ambiguous.
- `subagent` — delegate a task to a child agent with its own context window; only its final output returns here.

## Subagent roles

- `scout` (cheap) — read-only recon. Delegate wide codebase exploration so a compressed summary, not the files, lands in this context.
- `reviewer` (capable) — read-only review, correctness → security → reliability. It has no bash, so pass the diff text or the changed file paths in the task.

Children cannot see this conversation and cannot delegate further — make each task self-contained.
