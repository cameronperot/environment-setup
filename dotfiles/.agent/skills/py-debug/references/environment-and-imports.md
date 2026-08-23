# Environment and imports

Contents: [Which interpreter is running](#which-interpreter-is-running) · [Which file a module resolves to](#which-file-a-module-resolves-to) · [sys.path and env](#syspath-and-env) · [Installed-package truth](#installed-package-truth) · [Stale bytecode](#stale-bytecode) · [ModuleNotFoundError patterns](#modulenotfounderror-patterns) · [Circular imports and import-time hangs](#circular-imports-and-import-time-hangs)

## Which interpreter is running

```bash
uv run python -c 'import sys; print(sys.executable, sys.prefix)'
uv run python -VV
```

For "works in my shell, fails here" (or the reverse), run the same one-liner with bare `python` and compare; two different `sys.executable` values explain the whole discrepancy.

## Which file a module resolves to

```bash
uv run python -c 'import mod; print(mod.__file__)'
```

- A project file shadowing a stdlib or installed module (a local `queue.py`, `email.py`, `test.py`, `types.py`) is the classic cause; the signature errors are "AttributeError: partially initialized module" and "module 'x' has no attribute 'y'" for attributes that clearly exist.
- Check for same-named files where the script lives, because `sys.path[0]` (the script's directory) wins over site-packages: `ls *.py` next to the entry point.
- Namespace packages have no `__file__`; `print(mod.__path__)` shows which directories merged into the package.

## sys.path and env

```bash
uv run python -c 'import sys, pprint; pprint.pp(sys.path)'
env | grep -i python
```

A leaked `PYTHONPATH` pointing at another checkout silently wins over the project's own packages; unset it and rerun before debugging further.

## Installed-package truth

- `uv pip list` shows what is actually in the environment; `uv pip show -f pkg` shows the exact installed files.
- Compare against the imported reality: `uv run python -c 'import pkg; print(pkg.__version__, pkg.__file__)'`.
- **IF** the lockfile and environment have drifted **THEN** `uv sync` (state-changing: run it as a fix step, not as diagnosis) **ELSE** continue diagnosing elsewhere; `uv lock --check` tells you whether the lockfile itself is stale.

## Stale bytecode

- Symptoms: traceback line numbers that do not match the source you are reading, or a deleted module that still imports.
- Locate: `find . -name __pycache__ -type d -o -name '*.pyc'`.
- Fix by deleting them; python regenerates bytecode on the next run.

## ModuleNotFoundError patterns

| Pattern | Cause |
|---|---|
| Works after `uv sync`, not before | dependency present in `pyproject.toml` but environment stale |
| Only an optional feature's import fails | missing extra: `uv sync --extra name` |
| The project's own package not importable | missing editable install or wrong `[tool.uv]` / build config |
| Import works from repo root, fails elsewhere | cwd-relative import; run as a module: `uv run python -m pkg.mod`, not `uv run python pkg/mod.py` |
| Two distributions provide one namespace | namespace-package confusion; check `mod.__path__` for the merged directories |

## Circular imports and import-time hangs

- "cannot import name 'x' from partially initialized module" is a circular import; the traceback shows the cycle, and moving one import into the function that needs it breaks it.
- When an import hangs or is inexplicably slow, see where time is going (each line is cumulative microseconds per module):

```bash
timeout 60 uv run python -X importtime -c 'import mod' 2>&1 | tail -30
```
