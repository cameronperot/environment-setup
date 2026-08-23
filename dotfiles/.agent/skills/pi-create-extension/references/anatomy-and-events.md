# Extension anatomy and events

Contents: [Discovery and loading](#discovery-and-loading) · [Factory contract](#factory-contract) · [Imports](#imports) · [Event model](#event-model) · [Blocking and mutating events](#blocking-and-mutating-events) · [Notification-only events](#notification-only-events)

Verified against pi 0.84.1 (`@earendil-works/pi-coding-agent`); pi is pre-1.0 and the API changes between patch releases, so re-verify load-bearing details against the installed package (SKILL.md, API truth).

## Discovery and loading

- Auto-discovered from trusted locations: `~/.pi/agent/extensions/*.ts` and `~/.pi/agent/extensions/*/index.ts` (global); `.pi/extensions/*.ts` and `.pi/extensions/*/index.ts` (project, only after the project is trusted).
- Also loadable via the `extensions` and `packages` settings arrays, or `-e/--extension <path>` (repeatable, for quick tests); `--no-extensions` disables discovery but explicit `-e` still loads.
- Loaded via jiti: TypeScript runs without a build step; npm dependencies resolve from a sibling or parent `package.json` + `node_modules`; `node:` built-ins are available.
- `/reload` hot-reloads auto-discovered extensions only; `-e` extensions require a restart.

## Factory contract

- An extension is a default-export factory: `export default function (pi: ExtensionAPI): void | Promise<void>`.
- Async factories are awaited before startup continues (before `session_start`, `resources_discover`, and queued `registerProvider` flushes) — use them for one-time fetches such as discovering local models.
- Never start long-lived resources (sockets, watchers, timers) in the factory; start them in `session_start` and clean them up in an idempotent `session_shutdown`.

## Imports

- `@earendil-works/pi-coding-agent` — types (`ExtensionAPI`, `ExtensionContext`, events) and helpers (`isToolCallEventType`, `withFileMutationQueue`, `truncateHead`/`truncateTail`, `DEFAULT_MAX_BYTES`/`DEFAULT_MAX_LINES`, `CONFIG_DIR_NAME`, `defineTool`, `createLocalBashOperations`).
- `typebox` (bare specifier) — `Type` schemas for tool parameters.
- `@earendil-works/pi-ai` — `StringEnum` (required for string enums; `Type.Union`/`Type.Literal` break Google API compatibility), message types.
- `@earendil-works/pi-tui` — TUI components (`Text`, `Container`, `Key`, …) for custom renderers and `ctx.ui.custom()`.

## Event model

- Register handlers with `pi.on(event, handler)`; a handler is `(event, ctx) => result | undefined`, sync or async.
- For blocking/mutating events, return a result object to act and `undefined` to pass.
- Handlers run in extension load order; for `tool_call` the first block wins, `tool_result` is a middleware chain where each handler sees the previous patch, and `before_agent_start` chains the system prompt across extensions.

## Blocking and mutating events

| Event | Result / mutation | Notes |
|---|---|---|
| `project_trust` | `{trusted: "yes"\|"no"\|"undecided", remember?}` | Reduced ctx: only `{cwd, mode, hasUI, ui: {select, confirm, input, notify}}`; first yes/no wins and suppresses the built-in prompt; only global and `-e` extensions participate |
| `resources_discover` | `{skillPaths?, promptPaths?, themePaths?}` | Contribute extra resource paths; `event.reason` is `"startup"` or `"reload"` |
| `session_before_switch` / `session_before_fork` | `{cancel?: true}` | Veto the operation |
| `session_before_compact` | `{cancel?: true}` or a custom compaction/summary | E.g. delegate summarization to a cheaper model |
| `session_before_tree` | `{cancel?: true}` or a custom summary | |
| `before_agent_start` | `{message?, systemPrompt?}` | `systemPrompt` chains across extensions; `event.systemPromptOptions` exposes `customPrompt`, `selectedTools`, `toolSnippets`, `promptGuidelines`, `appendSystemPrompt`, `cwd`, `contextFiles`, `skills` — may contain full context-file contents, treat as sensitive |
| `context` | `{messages?}` | Runs before each LLM call; `event.messages` is a deep copy, so prune or inject there and return it — never assume in-place mutation propagates |
| `before_provider_headers` | none — mutate `event.headers` in place | A `null` value deletes a header |
| `before_provider_request` | any non-`undefined` return replaces the payload | Inspect or replace the raw request |
| `message_end` | `{message?}` | Replacement must keep the same `role` |
| `tool_call` | `{block?: true, reason?, terminate?}` | `event.input` is mutable in place with no re-validation; narrow with `isToolCallEventType(name, event)`; preflight runs sequentially even though execution is concurrent |
| `tool_result` | `{content?, details?, isError?, usage?}` | Middleware chain; partial patches allowed |
| `input` | `{action: "continue"}` \| `{action: "transform", text, images?}` \| `{action: "handled"}` | Fires after extension commands, before skill/template expansion |
| `user_bash` | `{operations?, result?}` | Intercept `!`/`!!`; wrap `createLocalBashOperations()` or return a result directly |

## Notification-only events

- Session: `session_start` (`reason: startup|reload|new|resume|fork`), `session_info_changed`, `session_compact`, `session_tree`, `session_shutdown` (`reason: quit|reload|new|resume|fork`).
- Agent and turns: `agent_start`, `agent_end`, `agent_settled` (nothing more will auto-run — use for status), `turn_start`, `turn_end`.
- Messages: `message_start`, `message_update`.
- Tool execution: `tool_execution_start`, `tool_execution_update`, `tool_execution_end`.
- Provider and model: `after_provider_response` (status + headers), `model_select`, `thinking_level_select`.
