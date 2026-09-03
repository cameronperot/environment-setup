---
name: pi-create-extension
description: Guides authoring Pi extensions — TypeScript factories that register tools, slash commands, event handlers, and UI via the ExtensionAPI. Use when explicitly asked to create or fix a Pi extension, add a custom tool or hook, or override a built-in tool. Not for prompt templates (pi-create-prompt) or skills (pi-create-skill).
disable-model-invocation: true
---

# pi-create-extension

An extension is a TypeScript file with a default-export factory `(pi: ExtensionAPI) => void | Promise<void>` that Pi loads via jiti — no build step — and that runs with full system permissions.

Trailing input after `/skill:pi-create-extension` describes the extension to create (behavior, tools, hooks) or names an existing extension to review or fix; with no input, derive the requirements from the conversation and ask for anything missing in one consolidated question.

## Confirm the genre

- Reusable prompt text the user expands, reviews, and edits before sending is a prompt template: switch to `/skill:pi-create-prompt`.
- Instructions, workflows, domain knowledge, or reference docs the agent loads when a task matches belong in a skill: switch to `/skill:pi-create-skill`.
- Tiebreak for "/name command" requests: a /name that inserts editable prompt text is a template; a /name that executes code or opens UI is an extension command.
- Behavior instructions cannot express — new tools, slash commands that run code, event interception, UI, providers, context injection — is an extension; continue here.
- Push back before building a tool: a registered tool costs tokens on every request, while a skill or plain CLI script costs nothing until used — prefer those when instructions suffice.

## API truth

Pi is pre-1.0 and the extension API changes between patch releases, so never author from memory or stale copies:

1. Read the bundled reference matching the work (see References); the references are verified at pi 0.84.1.
2. Locate the installed package: `PI_PKG="$(npm root -g)/@earendil-works/pi-coding-agent"`; if that path does not exist, walk up from `readlink -f "$(command -v pi)"` to find the package root.
3. Verify every load-bearing signature against `$PI_PKG/dist/core/extensions/types.d.ts`, and grep `$PI_PKG/docs/extensions.md` (~3,000 lines — search it, don't read it whole); `$PI_PKG/examples/extensions/` holds ~79 working examples.
4. Compare `pi --version` with the version stamped in the references; on any conflict the installed package wins, and note that a repo-vendored `node_modules` copy may be stale relative to the global install.

## Ground rules

- The factory only registers things; start long-lived resources in `session_start` and clean them up in an idempotent `session_shutdown`.
- Import `Type` from bare `typebox`; use `StringEnum` from `@earendil-works/pi-ai` for string enums, never `Type.Union`/`Type.Literal` (Google API compatibility).
- Tool results require `details` — pass `details: {}` at minimum; signal errors by throwing, since returning a value never sets the error flag.
- Truncate tool output (50KB/2,000-line caps; `truncateHead`/`truncateTail`).
- Wrap file read-modify-write in `withFileMutationQueue(absPath, fn)` — tools run concurrently.
- Pass `ctx.signal` (or the `execute` signal) into `fetch`/`pi.exec` so Esc cancels.
- Guard UI writes with `ctx.hasUI`, and `ctx.ui.custom()` with `ctx.mode === "tui"`; in json/print mode UI methods are no-ops and stdout may be a protocol stream.

## Scaffold

```typescript
/**
 * <Name> Extension
 *
 * <What it does and why it exists as an extension.>
 */
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";

export default function (pi: ExtensionAPI) {
	pi.registerTool({
		name: "greet",
		label: "Greet",
		description: "Greet someone by name",
		parameters: Type.Object({ name: Type.String({ description: "Name to greet" }) }),
		async execute(_toolCallId, params, _signal, _onUpdate, _ctx) {
			return { content: [{ type: "text", text: `Hello, ${params.name}!` }], details: {} };
		},
	});
}
```

Placement: a single `*.ts` file at the extensions root for simple extensions, or `<name>/index.ts` in its own subdirectory when it has multiple modules or its own npm dependencies (add a `package.json` and run `npm install` there).
Load paths: `~/.pi/agent/extensions/` (global), `.pi/extensions/` (project, after trust), `-e <path>` for tests; `/reload` hot-reloads the auto-discovered locations.

## References

- `references/anatomy-and-events.md`: discovery and loading, factory contract, imports, and the full 33-event catalog with each blocking event's return shape — read before writing any event hook.
- `references/tools-commands-context.md`: ToolDefinition fields, result and error rules, overriding built-ins, commands/shortcuts/flags, messaging, tool gating, and the ctx/ctx.ui surface — read before registering anything.
- `references/patterns-and-pitfalls.md`: state and lifecycle patterns, session-control footguns, concurrency, token economy, testing recipes, and version drift — read before validating.

## Workflow

1. Confirm the genre and the token-economy tradeoff.
2. Gather requirements: what to register (tools, commands, hooks, UI), state and persistence needs, target location.
3. Run the API truth steps for everything load-bearing.
4. Design: pick events (blocking vs notification-only), tool schemas, single file vs subdirectory.
5. Author from the scaffold, applying the ground rules; when working inside a config repo, apply the house integration below.
6. Run the validation loop until clean.
7. Report: what the extension registers, its per-request token cost (tool definitions and prompt snippets are paid every request), and how to install or enable it.

## House repo integration

Apply only when authoring inside a Pi config repo that has these files (e.g. this environment's `.pi/agent/extensions/`):

- Open the file with a block comment stating what the extension does and why; indent with tabs; import from `@earendil-works/pi-coding-agent` at the repo's pinned version range.
- Put policy shared across extensions in `shared/` modules rather than duplicating it.
- Add a new extension subdirectory to the `include` array in the repo's `tsconfig.json`, or it silently escapes typechecking.
- `npm run typecheck` must pass in the extensions directory.
- Update the repo's extension docs where they list or count extensions (e.g. `extensions/README.md` tables and any counts in the parent README), and check any documented load-order or conflict interactions.

## Validation loop

Run until a full pass is clean; fix the root cause and restart at 1 on any failure.

1. Typecheck: the repo's `npm run typecheck` if present; else `npx tsc --noEmit` when a `package.json` with the pi packages exists; else rely on the load test, since jiti surfaces compile errors at load.
2. Load test: `pi -e ./my-extension.ts -p "reply ok"` — factory and registration errors print at startup.
3. Functional check: invoke the tool or command once in a real session; for hooks, run `pi -e ./my-extension.ts --mode json -p "<prompt exercising the hook>"` and read the event stream.
4. Optional: repeatable tests via the SDK harness (`createAgentSession` + `DefaultResourceLoader`; see `$PI_PKG/docs/sdk.md`).
