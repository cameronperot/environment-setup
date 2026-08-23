---
name: py-conventions
description: Applies Python standards and idioms, uv execution, naming conventions, immutable typing, error handling, and docstrings. Always use when writing, editing, refactoring, or reviewing Python code, scripts, or modules.
---

# py-conventions

Target Python >= 3.14 with performant, Pythonic code adhering to strict environment, typing, error handling, and documentation conventions without worrying about backwards compatibility.

Trailing input after `/skill:py-conventions` specifies paths, symbols, or requirements to apply conventions to; with no input, apply conventions across the current Python context.

## Environment

- Execute all Python tools and scripts through `uv` (`uv run python`, `uv run pytest`, `uv run ruff`, `uv run ty`) so that the project virtual environment and pinned dependencies resolve properly.
- Never activate virtual environments manually or invoke bare `python`, `pip`, or tool binaries directly.

## Naming Conventions

- Name variables descriptively but not verbosely.
- Use underscores for subscripts (e.g. `my_var_1`, `my_var_2`).
- Prefix DataFrame variables with `df_` (e.g. `df_prices`, `df_orders`).

## Types and Annotations

- Prefer immutable types such as tuples over lists when collection contents do not change.
- Use PEP 585 built-in generics and PEP 604 union syntax (`dict[str, int]`, `list[str]`, `T | None`, `T1 | T2`) instead of importing `Dict`, `List`, `Optional`, or `Union` from `typing`.

## Idioms and Structure

- Format strings using f-strings; avoid `.format()` or `%` string formatting.
- Compare against `None` using identity checks (`is None` / `is not None`), never truthiness checks.
- Never use mutable default arguments in function or method definitions.
- Pass arguments by name whenever a function call takes more than one argument to prevent positional ambiguity.
- Keep functions concise, modular, and focused on a single responsibility.

## Error Handling

- Catch specific exception types; never use a bare `except:` or catch `Exception` indiscriminately.
- Log exceptions with `logger.exception()` inside `except` blocks rather than `logger.error()` to preserve traceback context.
- Handle caught exceptions cleanly or re-raise; never swallow errors silently.

## Docstrings and Comments

- Write Google-style docstrings for all public modules, classes, and functions, including `Args:`, `Returns:`, and `Raises:` sections where applicable.
- Write comments that explain why something is done rather than what the code is doing, using comments to demarcate distinct logical blocks.
- Keep comments succinct with no trailing periods unless multi-sentence, and avoid inline comments.
- Comments must always read as original and never explain something old or legacy that is no longer present.
