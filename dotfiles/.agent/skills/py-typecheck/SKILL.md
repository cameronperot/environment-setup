---
name: py-typecheck
description: Runs Astral's ty type checker (uv run ty check) and fixes diagnostics until it exits clean. Use when asked to type check, fix type errors, or fix type hints and annotations. Not for lint or style errors (py-lint-fix).
disable-model-invocation: true
---

# py-typecheck

Run ty (Astral's Python type checker) and fix what it reports.

Trailing input after `/skill:py-typecheck` names target paths or rule codes to focus on; with no input, check the whole project.

ty is the standard type checker here — use it even when the request says mypy or pyright.

## Setup

Run through uv so the project environment resolves:

- ty already a dev dependency → `uv run ty check`
- one-off run without installing → `uvx ty check`
- adding it to a project is a dependency change — ask first, then pin: `uv add --dev "ty==<version>"` (ty is pre-1.0; behavior shifts between 0.0.x releases)

## Workflow

1. Run `uv run ty check` from the repo root so config and `.venv` resolution work; add `--output-format concise` when the diagnostic count is large. Exit codes: 0 = clean, 1 = diagnostics at warning level or above, 2 = config/usage/IO error (surface it to the user, don't work around it), 101 = internal ty error (checker bug — report it, don't chase it).
2. Triage: group diagnostics by rule. For an unfamiliar rule, run `uv run ty explain rule <rule>`.
3. Fix environment problems first: `unresolved-import` / `unresolved-attribute` on installed packages usually mean a missing dependency, missing stubs, or the wrong interpreter (point ty at the right one with `--python <path>`). Unresolved modules produce `Unknown` types that cascade into downstream noise, so re-run after fixing them before judging anything else.
4. Apply autofixes: `uv run ty check --fix` (e.g., removes stale ignore comments), then review the diff — the tool is pre-1.0.
5. Fix the rest manually, definition sites before call sites: one corrected signature or attribute type clears many call-site diagnostics.
6. Re-run after each group of fixes until exit code 0.
7. If the project has tests, run `uv run pytest`. Type-driven edits can change runtime behavior (an added None-check alters control flow); report any failures honestly.

## Fix policy

Prefer fixes in this order:

1. Fix the code — the diagnostic is often a real bug.
2. Fix the annotation so it matches runtime reality.
3. Narrow: `isinstance`, `is None` checks, `match`, early returns; `TypeIs`/`TypeGuard` for reusable predicates.
4. `cast()` only at genuine knowledge boundaries (deserialization, framework magic), with a comment saying why it is safe.
5. Targeted `# ty: ignore[rule]` with a stated reason — last resort.

Never loosen a type to `Any` to silence a diagnostic. Never use a bare ignore or `--add-ignore` (it blanket-suppresses every diagnostic). Never edit ty config to silence a rule unless asked. Leave excluded, vendored, and generated code alone.

When a diagnostic contradicts runtime reality, verify (run the code path, read the stub) before concluding it is a false positive; ty is beta, so they happen. Suppress with `# ty: ignore[rule]` plus a comment naming the suspected checker bug — never contort correct code to please the checker.

## Rule-specific notes

- `possibly-unresolved-reference` (and the `possibly-missing-*` family): ignored by default, so if it fires the project opted in — fix by restructuring control flow (initialize before the branch, or raise in the else arm), don't suppress.
- `no-matching-overload`: usually a wrong argument type upstream; read the actual overloads before touching the call site.
- `unused-ignore-comment`: delete the stale ignore (`--fix` does this). Trap: this rule can only be suppressed by its own code, not by a bare `# ty: ignore` or `# type: ignore`.
- `division-by-zero`: ignored by default; if it fires, the project opted in — treat it as real.

## Suppression syntax

```python
x = f(arg)    # ty: ignore[invalid-argument-type]
y = g()       # ty: ignore[missing-argument, invalid-argument-type]
z: int = h()  # type: ignore[ty:invalid-assignment]  (scopes to ty in multi-checker repos)
```

- Place on the first or last line of a multi-line violation.
- File-level: the same comment on its own line before any code in the file.
- PEP 484 `# type: ignore` is honored but suppresses everything on the line — always use rule codes.
- `@no_type_check` suppresses a whole function (functions only); avoid it for the same reason.

## References

Read `references/configuration.md` when configuring ty (`[tool.ty.*]` / `ty.toml`), adopting it gradually in an existing codebase, wiring CI output or exit codes, or silencing rules for untyped third-party paths.
