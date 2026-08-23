# Patterns, pitfalls, and testing

Contents: [Lifecycle and state](#lifecycle-and-state) · [Session-control footguns](#session-control-footguns) · [Concurrency and cancellation](#concurrency-and-cancellation) · [Dynamic tool gating](#dynamic-tool-gating) · [Token economy](#token-economy) · [Testing](#testing) · [Debugging](#debugging) · [Version drift](#version-drift)

Verified against pi 0.84.1; read this file before validating any extension.

## Lifecycle and state

- The factory only registers things and does one-time fetches; start long-lived resources (sockets, watchers, timers) in `session_start` and clean them up in an idempotent `session_shutdown` — both fire again on `/reload`, fork, and resume.
- Branch-correct state: store turn state in tool-result `details` and rebuild it by replaying session entries (the shipped `todo.ts` pattern), so `/tree` navigation, forks, and resumes stay consistent; in-process variables silently reset on resume.
- `pi.appendEntry(customType, data)` persists data with the session without adding it to LLM context; the `context` event is the place to inject or prune what the model actually sees.

## Session-control footguns

- `withSession(ctx)` callbacks passed to `newSession`/`fork`/`navigateTree`/`switchSession` run after `session_shutdown` in the old extension closure: captured `pi`, `ctx`, and `sessionManager` references are stale and throw — capture plain data only and use the fresh context argument.
- Treat `ctx.reload()` as terminal (`await ctx.reload(); return;`); code after the await runs from the pre-reload version.
- Tools cannot call `reload()` (they get plain `ExtensionContext`); have the tool send a command instead: `pi.sendUserMessage("/mycmd", {deliverAs: "followUp"})`.
- `sendUserMessage` throws when the agent is streaming and no `deliverAs` is given; pick `"steer"`, `"followUp"`, or `"nextTurn"` explicitly for anything that can fire mid-turn.

## Concurrency and cancellation

- `tool_call` preflight runs sequentially, but tool execution is concurrent: a `tool_call` handler cannot see sibling results, and `tool_execution_end`/`tool_result` fire in completion order while the resulting messages emit in assistant source order.
- Wrap every file read-modify-write in `withFileMutationQueue(absPath, fn)`.
- Pass `ctx.signal` (or the `execute` signal argument) into `fetch`, `pi.exec`, and model calls so Esc actually cancels; expect it to be `undefined` outside turn events.
- Guard `getContextUsage()`: the result can be `undefined` and its `tokens`/`percent` fields are null right after compaction.

## Dynamic tool gating

- Register many tools but activate few: `pi.setActiveTools(names)` keeps per-request cost down; activations returned from a tool via `addedToolNames` are additive.
- Only one extension should drive `setActiveTools` — multiple drivers overwrite each other silently.
- Active-only `promptSnippet`/`promptGuidelines` text is rebuilt into the system prompt on changes, which invalidates the provider prompt-cache prefix; toggle sparingly.

## Token economy

- Every registered tool definition, `promptSnippet`, and `promptGuidelines` bullet is paid on every request, whether or not the tool is used.
- Prefer a skill or a plain CLI script when instructions suffice: a skill costs nothing until loaded, a tool costs tokens every turn.
- The real context sink is tool output, not definitions — truncate aggressively and keep results terse.

## Testing

1. Quick load test: `pi -e ./my-extension.ts -p "reply ok"` — factory and registration errors print at startup, and jiti surfaces compile errors here too.
2. Headless behavior test: `pi -e ./my-extension.ts --mode json -p "<prompt exercising the extension>"` — `hasUI` is false, UI methods are no-ops, and the stdout event stream shows tool calls, blocks, and injected messages.
3. Repeatable programmatic tests: `createAgentSession` + `new DefaultResourceLoader({additionalExtensionPaths: [...], extensionFactories: [...]})` from `@earendil-works/pi-coding-agent`; see `docs/sdk.md` in the installed package.
4. Functional check in a real session: invoke the tool or command once and confirm rendering, blocking, or injection behaves as intended.

## Debugging

- `console.log` output is visible in `--mode json` and in logs, not in the TUI transcript.
- Log the exact provider payload from a temporary `before_provider_request` handler when a prompt or tool schema looks wrong on the wire.
- Iterate with `/reload` (auto-discovered locations only); `-e` extensions need a restart per change.

## Version drift

- Pi is pre-1.0: events, fields, and helpers appear and disappear between patch releases.
- Before relying on a signature, confirm it in the installed package's `dist/core/extensions/types.d.ts` and `docs/extensions.md`; the installed version wins over this file, blog posts, and memory.
- A repo-vendored `node_modules` copy can lag the global install — e.g. a vendored 0.84.0 lacks `terminate` on `tool_call` block results, which 0.84.1 supports — so typechecking against the vendored types can pass while the runtime differs, and vice versa.
