# Registration surface and context

Contents: [ToolDefinition](#tooldefinition) · [Tool results and errors](#tool-results-and-errors) · [Overriding built-ins](#overriding-built-ins) · [Commands, shortcuts, flags](#commands-shortcuts-flags) · [Messaging and session helpers](#messaging-and-session-helpers) · [Tool gating and the rest of ExtensionAPI](#tool-gating-and-the-rest-of-extensionapi) · [ExtensionContext](#extensioncontext) · [ctx.ui](#ctxui) · [ExtensionCommandContext](#extensioncommandcontext)

Verified against pi 0.84.1; exact shapes live in the installed package's `dist/core/extensions/types.d.ts`.

## ToolDefinition

`pi.registerTool(definition)` works during load and after startup — new tools are callable immediately, no `/reload` needed.

| Field | Purpose |
|---|---|
| `name`, `label`, `description` | Identity and the LLM-facing description |
| `parameters` | typebox `TSchema` (`Type.Object(...)`); use `StringEnum` for string enums |
| `promptSnippet` | Optional one-line entry in the "Available tools" system-prompt section |
| `promptGuidelines` | Optional guideline bullets appended flat — each bullet must name its tool |
| `prepareArguments` | Optional shim that runs before schema validation (e.g. migrating args from resumed old sessions) |
| `executionMode` | `"sequential"` \| `"parallel"` per-tool override |
| `renderShell` | `"default"` \| `"self"` |
| `renderCall`, `renderResult` | Optional custom TUI renderers |
| `execute` | `(toolCallId, params, signal, onUpdate, ctx) => Promise<AgentToolResult>` |

`defineTool(tool)` preserves parameter type inference when a definition is assigned to a variable or collected in an array.

## Tool results and errors

- Result shape: `{content: (TextContent | ImageContent)[], details, usage?, addedToolNames?, terminate?}` — `details` is required, so pass `details: {}` at minimum.
- Signal errors by throwing from `execute`; returning a value never sets the error flag.
- Truncate output: built-in caps are 50KB / 2,000 lines; use `truncateHead`/`truncateTail` and `DEFAULT_MAX_BYTES`/`DEFAULT_MAX_LINES`.
- Tools run concurrently by default, so wrap any read-modify-write of a file in `withFileMutationQueue(absPath, fn)` (resolve to an absolute path first) or concurrent writes clobber each other.
- Honor the `signal` argument: pass it to `fetch`/`pi.exec` so Esc cancels the tool.

## Overriding built-ins

- Register the same name as a built-in (`read`, `bash`, `edit`, `write`, `grep`, `find`, `ls`) to override it; the result and `details` shape must match the built-in exactly or renderers and downstream consumers break.
- Renderer inheritance is per slot: omit `renderCall` and the built-in `renderCall` is used; `promptSnippet`/`promptGuidelines` are not inherited.
- Guards keyed on the tool name (e.g. `tool_call` handlers) still fire for the override.

## Commands, shortcuts, flags

- `pi.registerCommand(name, {description?, getArgumentCompletions?, handler})` — `handler(args: string, ctx: ExtensionCommandContext)`; `getArgumentCompletions(prefix)` returns `AutocompleteItem[] | null`.
- Duplicate command names get `/name:1`, `/name:2` suffixes; built-ins win over extension commands, which shadow same-named prompt templates.
- `pi.registerShortcut(key, {description?, handler})` — `key` is a `KeyId` from `@earendil-works/pi-tui`, not a free-form string.
- `pi.registerFlag(name, {type, description?, default?})` — only `type` (`"boolean"` \| `"string"`) is required; read with `pi.getFlag(name)`.

## Messaging and session helpers

- `pi.sendMessage(msg, {triggerTurn?, deliverAs?})` and `pi.sendUserMessage(content, {deliverAs?})` with `deliverAs: "steer" | "followUp" | "nextTurn"`; `sendUserMessage` throws if called while streaming without `deliverAs`.
- `pi.appendEntry(customType, data?)` persists data in the session without entering LLM context.
- `pi.setSessionName`/`getSessionName`, `pi.setLabel(entryId, label)`.
- `pi.exec(command, args, opts)` → `{stdout, stderr, code, killed}`.

## Tool gating and the rest of ExtensionAPI

- `pi.getActiveTools()`, `pi.getAllTools()` (each `ToolInfo` carries `sourceInfo.source`: builtin/sdk/extension — use it, don't path-parse), `pi.setActiveTools(names)`; additive activations from a tool result are recorded as `addedToolNames`.
- `pi.getCommands()` lists registered slash commands with provenance.
- `pi.registerProvider(...)`/`unregisterProvider`, `pi.registerMessageRenderer`, `pi.registerEntryRenderer`, `pi.registerMarkdownTransformer`.
- `pi.setModel`, `pi.getThinkingLevel`/`setThinkingLevel`.
- `pi.events` is an inter-extension event bus.

## ExtensionContext

- `ctx.mode`: `"tui" | "rpc" | "json" | "print"`; `ctx.hasUI` is true in tui and rpc — guard every UI write with it.
- `ctx.cwd`; build config paths with `CONFIG_DIR_NAME`, never a hardcoded `.pi`.
- `ctx.sessionManager` (read-only: `getEntries`, `getBranch`, `buildContextEntries`, `getLeafId`); `ctx.modelRegistry`, `ctx.model`, `ctx.scopedModels`, `ctx.thinkingLevel`.
- `ctx.signal`: abort signal for turn work — pass it to `fetch`/exec; typically defined during turn events and `undefined` in idle, command, and shortcut contexts.
- `ctx.isIdle()`, `ctx.isProjectTrusted()`, `ctx.abort()`, `ctx.hasPendingMessages()`, `ctx.shutdown()`, `ctx.compact(opts?)`, `ctx.getSystemPrompt()`.
- `ctx.getContextUsage()` → `{tokens: number | null, contextWindow, percent: number | null}` or `undefined`; `tokens` is null right after compaction — guard before arithmetic.

## ctx.ui

- Dialogs: `select(title, options, opts?)`, `confirm(title, message, opts?)`, `input(title, placeholder?, opts?)`, `editor(title, prefill?)`; `opts` is `{signal?, timeout?}` and on timeout select/input resolve `undefined`, confirm resolves `false`.
- `notify(msg, "info" | "warning" | "error")`.
- `custom(factory, {overlay?, overlayOptions?, onHandle?})` for full TUI components — guard with `ctx.mode === "tui"`, not just `hasUI`.
- Status and chrome: `setStatus(key, text)`, `setWidget(key, lines | factory, {placement})`, `setFooter`, `setHeader`, `setTitle`, `setWorkingMessage`, `setWorkingVisible`, `setWorkingIndicator`, `setHiddenThinkingLabel`.
- Editor and theming: `setEditorText`/`getEditorText`, `pasteToEditor`, `addAutocompleteProvider`, `setEditorComponent`/`getEditorComponent`, `theme`, `getAllThemes`/`getTheme`/`setTheme`, `getToolsExpanded`/`setToolsExpanded`, `onTerminalInput` (returns an unsubscribe).

## ExtensionCommandContext

- Command handlers get `ExtensionCommandContext`, which extends `ExtensionContext` with session control that would deadlock inside event handlers: `waitForIdle()`, `newSession(opts?)`, `fork(entryId, opts?)`, `navigateTree(targetId, opts?)`, `switchSession(path, opts?)`, `reload()`, `getSystemPromptOptions()`.
- The session-replacement calls return `{cancelled}` and accept a `withSession` callback — see `patterns-and-pitfalls.md` for the stale-closure footgun before using it.
