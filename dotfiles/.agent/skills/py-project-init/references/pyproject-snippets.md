# pyproject.toml tool blocks

Canonical `[tool.*]` blocks for py-project-init. Merge them into the pyproject.toml that `uv init` generated; add a block only for a tool that is actually being set up.

Contents:

1. ruff
2. ty
3. pytest
4. coverage

## 1. ruff

Stable rule families only — no `preview = true`, so behavior doesn't drift between ruff releases. Line length stays at ruff's default; set `line-length` only if the user asks.

```toml
[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "F",   # pyflakes
    "I",   # isort (import sorting)
    "UP",  # pyupgrade (modern syntax for the requires-python floor)
    "B",   # flake8-bugbear (likely bugs)
    "SIM", # flake8-simplify
    "RUF", # ruff-specific rules
]
```

## 2. ty

ty needs no configuration for a standard uv `src/` layout — it reads `requires-python` and finds `src/` on its own. Do not add a `[tool.ty]` table unless something misbehaves, and if ty rejects a config key, drop the key and run with zero config rather than guessing at settings.

## 3. pytest

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--cov --strict-markers --strict-config"
```

`--strict-markers` and `--strict-config` turn typo'd markers and config keys into errors instead of silent no-ops.

## 4. coverage

```toml
[tool.coverage.run]
source = ["src"]
branch = true

[tool.coverage.report]
show_missing = true
```

Coverage runs on demand (`uv run pytest --cov`); it is not part of the init validation loop.
