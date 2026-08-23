---
name: py-test-gen
description: Generates idiomatic pytest tests for Python code and runs them with uv until they pass; coverage-gap mode finds and covers untested lines. Use only when explicitly asked to write tests or add coverage. Do not invoke proactively after writing new Python code.
---

# py-test-gen

Generate behavior-first pytest tests and prove they work: every generated test is executed with `uv run pytest` and survives a vacuity check before the task is reported done.

## Arguments

Trailing input after `/skill:py-test-gen` selects the target and mode:

- A path, function name, or class name → default mode on that target.
- `coverage`, `gaps`, or a percentage → coverage-gap mode, scoped to any path also given.

Conversational requests map the same way: "test this function" → default mode; "what's untested" / "raise coverage" → coverage-gap mode.
With no input, take the target from the conversation, else from `git diff` and `git status` (recently changed Python files); if still ambiguous, ask one question — don't guess.

## Environment rules

- Run every Python command through uv: `uv run pytest`, `uv run ruff`. Never bare `python`/`pip`, never another runner.
- Verify dependencies before starting: `uv run pytest --version`; for coverage-gap mode also `uv run pytest --cov --help` (needs pytest-cov). If missing, ask the user before running `uv add --dev pytest pytest-cov`.
- Discover project conventions before writing anything: test layout (`tests/` mirror vs `test_*.py` alongside the source), shared fixtures in `conftest.py`, `[tool.pytest.ini_options]` in `pyproject.toml`, existing naming style. New tests must look native to the repo.

## Workflow (default mode)

1. Read the code under test in full, plus its immediate callees, any existing tests for the module, and every `conftest.py` on the path to it.
2. Map behaviors before writing: list the observable behaviors, input classes, edge cases, and error paths as a short checklist. This list drives the tests — not the implementation's branch structure.
3. Write tests per `## Test rules`, placed per the project layout.
4. Run `uv run pytest <new-file> -x -q`.
5. On failure, decide whether the test or the code under test is wrong. If a test exposes a real bug: report the bug to the user and mark the test with a comment. Never bend a test — or silently patch the code — to make it pass.
6. Run `## Validation loop`; repeat steps 4–6 until everything passes.

## Workflow (coverage-gap mode)

1. Run exactly: `uv run pytest --cov=<target> --cov-branch --cov-report=term-missing -q`.
2. Read the Missing column; open each uncovered region and classify it: untested branch, untested error path, or dead code.
3. Prioritize public API and error handling. Skip trivia (`__repr__`, `if __name__ == "__main__"` guards). Flag dead code for removal — do not test it.
4. For each gap, run default-mode steps 1–6 scoped to that behavior.
5. Re-run the coverage command; confirm the targeted lines and branches are now covered.
6. Coverage is a floor, not a target. Never add assertion-free or tautological tests to move the number. Report any gaps deliberately left open and why.

## Test rules

### What to test

- Test behavior, not implementation: assert on return values and observable effects, never on private attributes or the call sequence of internals.
- One behavior per test. The name alone should say why the test could fail.
- Assert concrete values: `assert result == [3, 1]`, not `assert result` or an `isinstance` check.
- No tautological tests: no asserting a mock returns what it was configured to return, no `assert x == x`, no test without an assertion.
- Error paths are first-class: `pytest.raises(ExcType, match="...")`. `match=` is required so the test pins which error, not just an error.

### Structure

- Arrange-Act-Assert, separated by blank lines; one Act per test.
- Name tests `test_<unit>_<scenario>_<expected>` (e.g. `test_parse_order_empty_symbol_raises_value_error`).
- Use `@pytest.mark.parametrize` instead of copy-pasted near-identical tests; add `ids=` when the parameters aren't self-describing. Don't parametrize unrelated behaviors together.
- Fixtures only for setup shared by 2+ tests or needing teardown — not for one-test setup, and never where they hide the Arrange step. Prefer a plain builder function when a fixture would add indirection without teardown.
- No logic in tests: a loop over cases means you wanted `parametrize`; a branch means you wanted two tests.

### Inputs

Walk this edge-case checklist for every unit: empty, `None`, boundaries (0, 1, max, off-by-one), duplicates, unicode/whitespace, very large inputs, negative numbers, wrong-but-plausible types where the contract cares.

### Determinism and isolation

- Deterministic always: freeze or inject time, seed every RNG, no sleep-based waits, no network, `tmp_path` instead of real paths, `monkeypatch.setenv`/`delenv` for environment variables.
- Order-independent: no shared mutable state between tests; each test must pass when run alone by node-id (`uv run pytest path/to/test.py::test_name`).

### Mocking (headlines — details in references/mocking-and-isolation.md)

- Mock at system boundaries only: network, database, clock, subprocess. Prefer a small fake over `MagicMock`. Don't mock what you own; never mock internals of the module under test.
- Mock-call assertions (`assert_called_once_with`) supplement value assertions. A test whose only assertion is about a mock is testing the mock.

### Coverage

Coverage is a floor, not a target. Uncovered dead code gets flagged for deletion, not tested.

## Example shape

```python
import pytest

from orders.parser import parse_order


@pytest.fixture
def raw_order():
    return {"symbol": "BTC/USDT", "side": "buy", "qty": "0.5"}


def test_parse_order_valid_input_returns_order(raw_order):
    order = parse_order(raw_order)

    assert order.symbol == "BTC/USDT"
    assert order.qty == pytest.approx(0.5)


@pytest.mark.parametrize(
    ("qty", "expected"),
    [("1", 1.0), ("0.001", 0.001), ("1e-8", 1e-8)],
    ids=["integer", "decimal", "scientific"],
)
def test_parse_order_qty_formats_parses_to_float(raw_order, qty, expected):
    raw_order["qty"] = qty

    order = parse_order(raw_order)

    assert order.qty == pytest.approx(expected)


def test_parse_order_empty_symbol_raises_value_error(raw_order):
    raw_order["symbol"] = ""

    with pytest.raises(ValueError, match="symbol"):
        parse_order(raw_order)
```

## Validation loop

1. Run `uv run pytest <new-file> -q`. All tests pass; warnings acceptable only if pre-existing.
2. Vacuity check (mandatory, once per new test file): change one expected value in the most important test to something deliberately wrong, re-run, confirm it fails, revert. If it still passes, the test is vacuous — fix it before proceeding. For property-based tests, weaken the property instead.
3. Fail-then-pass where feasible: when the tests target code changed in this session, run them against the pre-change code (`git stash` → run → `git stash pop`) to confirm red-then-green. Skip for long-standing code; step 2 substitutes.
4. Run the new tests together with the module's existing tests to catch ordering or isolation breakage, then run one new test alone by node-id.
5. If ruff is in the project: `uv run ruff format <file>` then `uv run ruff check <file>`. Otherwise match the surrounding style by hand — never introduce a formatter the project doesn't use.
6. Coverage-gap mode only: re-run the coverage command and confirm the targeted lines now show covered.
7. Report: test names added, behaviors covered, any bugs found (with the failing test as evidence), and any gaps deliberately left with the reason.

## When the code resists testing

If code can't be tested without refactoring — hard-coded I/O, module-level side effects, global state — propose the minimal seam to the user (usually parameter injection) instead of deep-mocking around it. A test that needs three nested patches is a design report, not a test.

## Escape hatch

If the user explicitly asks for something different — unittest style, doctests, no fixtures, a specific layout, tests for private helpers — their instruction wins over these defaults. The validation loop (write → run → vacuity-check) still applies; it is the non-negotiable part.

## References

- `references/property-based.md` — read when the user asks for property-based or Hypothesis tests, or when the target is a pure function over structured input (parsers, encoders, codecs, math) where properties beat examples.
- `references/mocking-and-isolation.md` — read when the code under test touches network, database, filesystem beyond `tmp_path`, subprocess, time, randomness, or environment variables.
