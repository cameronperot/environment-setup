# Memory leaks

Contents: [Confirm growth](#confirm-growth) · [tracemalloc](#tracemalloc) · [gc inspection](#gc-inspection) · [Usual suspects](#usual-suspects)

## Confirm growth

Cheap RSS observation before any tooling; a flat line means no leak and the investigation ends here.
Get `$pypid` by backgrounding the process and resolving the interpreter PID as shown in `references/hangs-crashes-async.md` (Confirm the hang).

```bash
for i in $(seq 12); do ps -o rss= -p "$pypid"; sleep 5; done
```

In-process equivalent (peak RSS in KiB on Linux, printed from a loop the program already has):

```python
print(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
```

## tracemalloc

Start tracing with call-stack depth 25, either from launch or via env var:

```bash
uv run python -X tracemalloc=25 app.py </dev/null
PYTHONTRACEMALLOC=25 uv run python app.py </dev/null
```

Take two snapshots around the suspected activity (for example, before and after N iterations of the leaking loop) and diff them:

```python
snap1 = tracemalloc.take_snapshot()
# ... run the suspected iterations ...
snap2 = tracemalloc.take_snapshot()
for stat in snap2.compare_to(snap1, "lineno")[:15]:
    print(stat)
```

For the worst offender, switch the key to full tracebacks to see the allocation path, not just the line:

```python
top = snap2.compare_to(snap1, "traceback")[0]
print("\n".join(top.traceback.format()))
```

## gc inspection

- Type histogram diffed before and after the suspected activity shows *what* accumulates:

```python
print(Counter(type(o).__name__ for o in gc.get_objects()).most_common(20))
```

- `gc.collect()` returns the number of unreachable objects found; a large number every cycle points at reference cycles being created continuously.
- `gc.set_debug(gc.DEBUG_SAVEALL)` keeps collected garbage in `gc.garbage` for inspection instead of freeing it.
- `gc.get_referrers(obj)` answers "who is keeping this alive"; use it on one representative object, not in a loop, because it is slow and returns huge results.
- Count survivors of one suspect class with a `weakref.WeakSet`: add every constructed instance, and if `len()` keeps growing after collections, those instances are being retained.

## Usual suspects

- Module-level caches and registries that only ever grow.
- `functools.lru_cache` on a method, which keeps every `self` alive through the cache.
- Stored exception objects, which keep their whole traceback and every frame's locals alive.
- Handler, callback, or listener lists that are appended to but never pruned.
- Asyncio tasks accumulated in a collection (or leaked via `create_task` without cleanup) that never finish.
