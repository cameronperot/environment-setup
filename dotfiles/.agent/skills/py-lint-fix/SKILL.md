---
name: py-lint-fix
description: Fixes Python lint errors with ruff and formats with ruff format until ruff check passes. Use when asked to lint Python code, fix ruff errors, or pass CI lint checks. Not for type errors (py-typecheck).
disable-model-invocation: true
---

# py-lint-fix

Fix Python lint errors with ruff, then format. Run ruff through the project's environment: `uv run ruff` by default; if the project does not use uv, invoke `ruff` via the project's own environment instead.

Trailing input after `/skill:py-lint-fix` names target paths or rule codes to focus on; with no input, lint the whole project.

## Workflow

1. Survey the damage: run `uv run ruff check` from the repo root so config resolution works. Respect the project's config (`pyproject.toml` / `ruff.toml` / `.ruff.toml`); never pass `--select` or `--ignore` to change what is checked. When the violation count is large, run `uv run ruff check --statistics` to plan the work rule by rule.
2. Apply safe auto-fixes: `uv run ruff check --fix`. Safe fixes preserve semantics and need no review.
3. Handle unsafe fixes: preview with `uv run ruff check --unsafe-fixes --diff` and review every hunk for semantic changes — e.g. F841 deletes an assignment even when its right-hand side has side effects. **IF** all hunks are semantically safe **THEN** apply with `uv run ruff check --fix --unsafe-fixes` **ELSE** fix those spots manually and leave the unsafe fixer alone.
4. Manually fix whatever remains. Fix the root cause of each violation; do not silence it.
5. Re-run `uv run ruff check` and repeat steps 2–4 until it exits 0. Exit 1 means violations remain; exit 2 means a config or usage error — surface that to the user, don't work around it.
6. Format: run `uv run ruff format`, then one final `uv run ruff check` to confirm formatting reintroduced nothing.
7. Verify behavior: if the project has a test suite, run it (`uv run pytest`). Report failures honestly rather than papering over them — auto-fixes, especially unsafe ones, can change behavior.

## Fix policy

- Never add a bare `# noqa`. Use rule-specific `# noqa: <CODE>` only for genuine false positives, and state the justification when you add one.
- Never edit lint configuration to silence rules unless the user explicitly asks.
- Leave excluded, vendored, and generated code alone.
- Some E501 violations survive `ruff format` (long string literals, comments, URLs) — fix those manually by restructuring the line.
