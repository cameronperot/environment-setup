# pdb and tracebacks

Contents: [Reading tracebacks](#reading-tracebacks) · [Non-interactive pdb](#non-interactive-pdb) · [Instrumentation](#instrumentation) · [Strictness switches](#strictness-switches)

## Reading tracebacks

- The bottom frame is the raise site; the frames above it are the call path that led there.
- Chained exceptions print oldest first, so the first traceback in the output is usually the root cause; the last one is just where it surfaced.
- `raise X from Y` sets `__cause__` and prints "The above exception was the direct cause of the following exception".
- An exception raised while handling another sets `__context__` and prints "During handling of the above exception, another exception occurred".
- Walk a chain programmatically when the printed output is truncated or swallowed:

```python
while e:
    print(type(e).__name__, e)
    e = e.__cause__ or e.__context__
```

- Inside an `except` block, `traceback.print_exception(e)` or `traceback.format_exc()` captures the full chain when a handler is hiding it.

## Non-interactive pdb

pdb executes `-c` commands as if typed at the prompt and holds unconsumed ones for the next prompt, so a whole breakpoint session can be scripted from the command line.
End every queue with `q`, because after a normal program exit pdb restarts the program and prompts again.
Append `</dev/null` as a belt-and-braces EOF so a mistake in the queue cannot hang the session.

Breakpoint and inspect:

```bash
uv run python -m pdb -c 'b mymod.py:42' -c c -c 'pp locals()' -c 'p x, type(x)' -c w -c q script.py </dev/null
```

Conditional breakpoint (stop only when the condition holds):

```bash
uv run python -m pdb -c 'b mymod.py:42, x is None' -c c -c 'pp locals()' -c w -c q script.py </dev/null
```

Post-mortem on an uncaught exception (`c` runs to the crash, then the queue executes at the crash frame):

```bash
uv run python -m pdb -c c -c w -c 'pp locals()' -c u -c 'pp locals()' -c q script.py </dev/null
```

Command cheat-list for queues: `p` print, `pp` pretty-print, `w` where, `l` list source, `u`/`d` move up/down a frame, `b` break, `c` continue, `q` quit.
Never queue `interact`; it opens a REPL that waits for input.

If the code already contains a `breakpoint()` call, drive it with piped stdin or neutralize it:

```bash
printf 'pp locals()\nw\nc\n' | uv run python script.py
PYTHONBREAKPOINT=0 uv run python script.py </dev/null
```

Prefer `-c` queues over piped stdin, because stdin is shared with the program under test and piping breaks any program that reads input.

To inspect the crash frame of an exception that a library or framework catches for you, add a temporary handler at the call site instead of pdb:

```python
except Exception:
    tb = sys.exc_info()[2]
    while tb.tb_next:
        tb = tb.tb_next
    print(traceback.format_exc())
    print(tb.tb_frame.f_locals)
    raise
```

## Instrumentation

- Prefer a temporary log line over print in threaded or async code; timestamps and thread names make interleaved output readable:

```python
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(threadName)s %(name)s %(levelname)s %(message)s",
)
```

- Enable one library's logger instead of global DEBUG when only that library is suspect: `logging.getLogger("urllib3").setLevel(logging.DEBUG)`.
- `print(f"{x=!r}")` prints the expression name and its repr; add `type(x)` and `id(x)` when two objects might be getting confused for one.
- Instrumentation is a probe, not a fix; remove it in the same session.

## Strictness switches

- `uv run python -X dev script.py </dev/null` enables dev mode (faulthandler, asyncio debug, extra warnings, ResourceWarning) and is the best first rerun for any unexplained failure.
- `uv run python -W error script.py </dev/null` turns warnings into exceptions with a traceback at the emission site; `PYTHONWARNINGS=error` is the env-var equivalent.
- Escalate selectively when full `-W error` is too noisy, for example `-W error::DeprecationWarning`.
