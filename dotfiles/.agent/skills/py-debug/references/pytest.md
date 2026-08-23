# pytest debugging

Contents: [Golden rerun](#golden-rerun) · [Flag glossary](#flag-glossary) · [Hanging tests](#hanging-tests) · [Flaky tests](#flaky-tests) · [Regressions with git bisect](#regressions-with-git-bisect) · [pytest not installed](#pytest-not-installed)

## Golden rerun

```bash
uv run pytest --lf -x -l --tb=long
```

- `--lf` reruns only what failed last time, `-x` stops at the first failure, `-l` prints each frame's locals in the traceback, `--tb=long` shows the full traceback.
- Never use `--pdb` or `--trace`; they open an interactive prompt and hang the session, and `-l --tb=long` shows the same locals without a prompt.
- Then narrow to one test by node id, quoting parametrized ids because the brackets are shell globs:

```bash
uv run pytest -x -l 'tests/test_foo.py::test_bar[case-3]'
```

## Flag glossary

| Flag | Use |
|---|---|
| `-vv` | full assertion diffs without truncation |
| `-s` | show print and logging output live |
| `-k "expr"` | select tests by keyword expression |
| `--maxfail=3` | stop after three failures |
| `-ra` | end-of-run summary of every non-passing outcome |
| `--collect-only -q` | list what would run without running it |
| `--setup-show` | show fixture setup and teardown order |
| `--fixtures` | list available fixtures and their origins |
| `-o log_cli=true --log-cli-level=DEBUG` | stream log records during the run |
| `-W error` | warnings become test failures |

## Hanging tests

- `timeout 300 uv run pytest -x -o faulthandler_timeout=60` makes pytest's built-in faulthandler plugin dump every thread's stack for any test running longer than 60 seconds, with an outer guard so the session never stalls.
- The dump names the hung test and the exact line it is blocked on; from there follow `references/hangs-crashes-async.md` if the blockage is a deadlock or a stuck event loop.
- `timeout` exits 124 when it had to kill the run; treat that exit code as confirmation of the hang, not as a test failure.

## Flaky tests

- Run the test alone, then in the full suite; a test that passes alone but fails in the suite is being polluted by shared state from an earlier test, so bisect the test order, not the test.
- Fix hash order: `PYTHONHASHSEED=0 uv run pytest -x 'tests/test_foo.py::test_bar'`.
- Seed randomness in a fixture so reruns are deterministic: `random.seed(0)` and, if used, `numpy.random.seed(0)`.
- If pytest-randomly is installed, `-p no:randomly` disables the shuffling and `--randomly-seed=<n>` replays a specific order.
- `--cache-clear` rules out stale `.pytest_cache` state; `-p no:cacheprovider` disables it entirely.
- Estimate the failure rate with a bounded repetition loop:

```bash
for i in $(seq 20); do uv run pytest -x -q 'tests/test_foo.py::test_bar' || break; done
```

## Regressions with git bisect

Exact sequence; the `sh -c` wrapper returns 125 (skip this commit) when the environment cannot even be built, so dependency drift at old commits is not misread as "bad":

```bash
git bisect start
git bisect bad
git bisect good <sha>
git bisect run sh -c 'uv sync -q || exit 125; uv run pytest -x -q "tests/test_foo.py::test_bar"'
git bisect reset
```

- If the test does not exist at the good commit, write a standalone reproducer script outside the repo (e.g. `/tmp/repro.py`) and bisect with `uv run python /tmp/repro.py` instead.
- `git bisect run` treats exit 0 as good, 1–124 and 126–127 as bad, and 125 as skip; make sure the reproducer cannot fail for unrelated reasons.

## pytest not installed

When pytest is not a project dependency, run it as an ephemeral extra instead of installing it:

```bash
uv run --with pytest pytest -x -l --tb=long
```
