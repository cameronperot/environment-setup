---
name: py-debug
description: Debugs Python code and pytest suites in uv-managed projects non-interactively — tracebacks, failing/flaky/hanging tests, scriptable pdb, hangs and segfaults, asyncio issues, memory leaks, import problems, regressions. Use only when explicitly asked to debug or investigate such a failure. Do not invoke proactively when an error or traceback appears in output.
disable-model-invocation: true
compatibility: Requires uv on PATH. py-spy is optional (live hang dumps); stdlib faulthandler is the fallback.
---

# py-debug

Systematic, non-interactive debugging of Python programs and pytest suites, with every command run through uv.

Trailing input after `/skill:py-debug` is the symptom description — enter the routing table with it; with no input, debug the most recent failure in the conversation.

## Ground rules

You cannot answer a debugger prompt, so any command that waits for input hangs the session.
Never use `pytest --pdb` or `pytest --trace`, never run `python -m pdb` without a `-c` command queue ending in `q`, and never start a REPL.
Append `</dev/null` when unsure whether a command reads stdin, and wrap anything that might hang in `timeout N`.
Always use `uv run python` and `uv run pytest`, never bare `python` or `pytest`; running the wrong interpreter is itself a common bug this skill diagnoses.
Remove all instrumentation (prints, log lines, breakpoints, watchdogs) once the bug is fixed.

## Core loop

1. Reproduce: pin one exact failing command and rerun it to confirm the failure; save it, because it is the verifier for every later step.
2. Read the evidence: read the full traceback bottom-up; in chained output the first traceback printed is usually the root cause (see `references/pdb-and-tracebacks.md`).
3. Localize: shrink to the smallest input, single test, or shortest script that still fails before theorizing.
4. Hypothesize: name one falsifiable cause at a time.
5. Instrument: apply the cheapest probe that discriminates the hypothesis, chosen from the routing table below.
6. Verify: the reproducer passes, then the relevant test suite passes; a surprising probe result means return to step 4, not add more probes.
7. Lock in: add a regression test that fails without the fix, then strip all instrumentation.

## Symptom routing

| Symptom | First command | Details |
|---|---|---|
| Exception, traceback | `uv run python -X dev script.py </dev/null`, read bottom-up | `references/pdb-and-tracebacks.md` |
| Why is this None / wrong value | pdb `-c` breakpoint queue or one log line at the suspect site | `references/pdb-and-tracebacks.md` |
| Failing pytest test | `uv run pytest --lf -x -l --tb=long` | `references/pytest.md` |
| Flaky / order-dependent test | run the test alone, then in the suite; fix seeds | `references/pytest.md` |
| Test suite hangs | `timeout 300 uv run pytest -x -o faulthandler_timeout=60` | `references/pytest.md` |
| Regression ("worked before") | `git bisect run` with the failing test | `references/pytest.md` |
| Script hangs / never exits | `timeout 60 uv run python script.py; echo $?` to confirm, then a stack dump | `references/hangs-crashes-async.md` |
| Deadlock (threads / locks) | all-thread dump: `kill -ABRT` on a `-X faulthandler` process, or `py-spy dump` | `references/hangs-crashes-async.md` |
| Segfault / fatal crash | `uv run python -X faulthandler script.py </dev/null` | `references/hangs-crashes-async.md` |
| Asyncio: stuck task, never awaited, destroyed but pending | `PYTHONASYNCIODEBUG=1 uv run python app.py </dev/null` | `references/hangs-crashes-async.md` |
| Memory grows without bound | `uv run python -X tracemalloc=25 app.py` plus snapshot diff | `references/memory-leaks.md` |
| ImportError / wrong module resolved | `uv run python -c 'import m, sys; print(m.__file__, sys.executable)'` | `references/environment-and-imports.md` |
| Behavior differs between shells or machines | compare `sys.executable`, `uv pip list`, env vars | `references/environment-and-imports.md` |

## References

- `references/pdb-and-tracebacks.md`: reading tracebacks and exception chains, non-interactive pdb recipes, instrumentation, strictness switches.
- `references/pytest.md`: rerun and isolation flags, hanging tests, flaky tests, git bisect for regressions.
- `references/hangs-crashes-async.md`: confirming hangs, live stack dumps (py-spy and faulthandler), deadlocks, segfaults, asyncio debugging.
- `references/memory-leaks.md`: confirming growth, tracemalloc snapshots, gc inspection, usual suspects.
- `references/environment-and-imports.md`: interpreter and venv identity, module shadowing, stale bytecode, ModuleNotFoundError patterns, import-time hangs.

When no routing row fits, pick the closest reference from this list and scan its table of contents.

## Optional: py-spy

py-spy dumps the stack of a live process without killing it, which nothing in the stdlib can do for a process that was started without faulthandler enabled.
Check availability and install on demand: `py-spy --version || uv tool install py-spy`.
If py-spy is unavailable or blocked by ptrace restrictions, use the faulthandler signal route in `references/hangs-crashes-async.md` instead.
