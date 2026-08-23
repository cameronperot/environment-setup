# Hangs, crashes, and asyncio

Contents: [Confirm the hang](#confirm-the-hang) · [Dump a live process](#dump-a-live-process) · [Deadlocks](#deadlocks) · [Segfaults and fatal crashes](#segfaults-and-fatal-crashes) · [Asyncio](#asyncio)

## Confirm the hang

Establish that the process really hangs, and how long it survives, before dumping anything:

```bash
timeout 60 uv run python script.py </dev/null; echo "exit=$?"
```

- Exit 124 means `timeout` killed it: a real hang or something much slower than expected.
- Use `timeout -k 5 60` when the process ignores SIGTERM.
- To probe a hang while it is happening, background the process and find the interpreter PID; `$!` can be uv's wrapper process rather than python itself, so resolve it with pgrep:

```bash
uv run python -X faulthandler script.py </dev/null &
sleep 5
pypid=$(pgrep -nf script.py)
```

## Dump a live process

Two routes; pick by whether the process must survive.

**py-spy (process survives).**

```bash
py-spy --version || uv tool install py-spy
py-spy dump --pid "$pypid"
```

- `--locals` adds local variables per frame; `--native` adds C-extension frames.
- On hardened kernels ptrace may be restricted (yama); retry with `sudo py-spy dump --pid "$pypid"`, and if that is unavailable use the faulthandler route below.

**Stdlib faulthandler (process dies, which is fine for diagnosis).**
Works only if the process was started with `-X faulthandler` (or `PYTHONFAULTHANDLER=1`); SIGABRT then prints every thread's stack before dying:

```bash
kill -ABRT "$pypid"
wait
```

In-code variants when you can edit the program:

- Non-fatal, dump on demand: `faulthandler.register(signal.SIGUSR1)` near startup, then `kill -USR1 "$pypid"` dumps all threads and the process keeps running.
- Watchdog from the start: `faulthandler.dump_traceback_later(30, exit=True)` prints all stacks and exits if the program is still alive after 30 seconds.
- Periodic self-dump for long-lived services:

```python
def dump_all_stacks():
    for tid, frame in sys._current_frames().items():
        print(f"--- thread {tid} ---")
        traceback.print_stack(frame)
```

## Deadlocks

- In the all-thread dump, look for two or more threads each sitting inside `lock.acquire` (or `Queue.get`, `Event.wait`) whose stacks show they hold what the other wants; inconsistent lock acquisition order is the usual root cause.
- `threading.enumerate()` printed from a watchdog names every live thread; name threads at creation so dumps are readable.
- Log with `%(threadName)s` in the format string while reproducing, so the interleaving that leads into the deadlock is visible.

## Segfaults and fatal crashes

- Rerun under faulthandler to get the Python stack at the fatal signal:

```bash
uv run python -X faulthandler script.py </dev/null
```

- The dump points at the C extension involved; confirm by importing suspects one at a time: `uv run python -X faulthandler -c 'import suspect'`.
- Check for recently changed native wheels with `uv pip list` (numpy, pandas, and friends built against mismatched ABIs are frequent offenders).
- Last resort, a one-shot non-interactive gdb backtrace of the C stack:

```bash
timeout 120 gdb -batch -ex run -ex bt --args "$(uv run python -c 'import sys; print(sys.executable)')" script.py
```

## Asyncio

Enable debug mode; three equivalent switches:

```bash
PYTHONASYNCIODEBUG=1 timeout 60 uv run python app.py </dev/null
timeout 60 uv run python -X dev app.py </dev/null
```

or in code, `asyncio.run(main(), debug=True)`; for an app that must keep running past the observation window, background it as in [Confirm the hang](#confirm-the-hang) instead of using `timeout`.

Debug mode reports:

- Coroutines that were never awaited, with the traceback of where they were created.
- Callbacks and tasks blocking the event loop longer than `slow_callback_duration` (default 0.1s); lower it to hunt loop blockers: `asyncio.get_running_loop().slow_callback_duration = 0.05`.
- Non-threadsafe calls made from the wrong thread (`call_soon` instead of `call_soon_threadsafe`).

Specific symptoms:

- "coroutine ... was never awaited": a missing `await` or a bare `foo()` where `asyncio.create_task(foo())` was intended; `-W error::RuntimeWarning` turns the warning into a traceback at the call site.
- "Task was destroyed but it is pending!": the task lost its last strong reference (keep the result of `create_task` in a collection) or the loop shut down before the task finished.
- A stuck task: py-spy and faulthandler only show the event-loop thread blocked in `select`/`epoll` or a rogue sync call; suspended coroutines are invisible to them, so dump the tasks from inside the loop:

```python
def dump_tasks(loop):
    for t in asyncio.all_tasks(loop):
        t.print_stack()

# near startup, inside the running loop:
loop = asyncio.get_running_loop()
loop.add_signal_handler(signal.SIGUSR1, dump_tasks, loop)
```

then `kill -USR1 "$pypid"` prints where every task is suspended.
A periodic variant (a coroutine that sleeps and calls `dump_tasks` in a loop, started with `create_task`) works where signals are awkward, such as on worker threads.
