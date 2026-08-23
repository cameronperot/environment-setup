# Pi Agent Configuration

The global Pi configuration, deployed to `~/.pi/agent/`. Everything here applies to every session in every directory.

Project-level files layer on top rather than replacing this: a repo's `AGENTS.md` / `CLAUDE.md` adds to [`AGENTS.md`](#agentsmd), and `<cwd>/.pi/guard-rules.json` is consulted before [`guard-rules.json`](#guard-policy).

## Layout

| Path | What it configures |
|---|---|
| `settings.json` | Provider, default model, default tool set, npm packages, TUI |
| `models.json` | Per-provider overrides — OpenRouter routing only |
| `guard-rules.json` | Path and bash-command policy the guard extensions enforce |
| `AGENTS.md` | Prepended to every request; describes the extension tools and the subagent roles |
| `extensions/` | 21 local extensions plus shared modules — see [`extensions/README.md`](extensions/README.md) |

## Models and providers

The default provider, model and `thinkingLevel` live in `settings.json` and change often — read them there rather than assuming.

`models.json` carries one thing: OpenRouter routing pinned to `data_collection: deny` and `zdr: true`. That is a privacy floor for every request regardless of which model is selected, and it is kept separate from `settings.json` because it is provider policy rather than a preference. `enableInstallTelemetry` is off.

## Presets

The `preset` extension (`preset.ts`) reads named presets from `~/.pi/agent/presets.json`, with `<cwd>/.pi/presets.json` overriding by name, and switches provider, model, thinking level, tool set and instructions via `/preset`, `--preset` or Ctrl+Shift+U. A preset's `instructions` are appended to the system prompt while it is active, so they cost tokens only then.

No `presets.json` exists, so no presets are defined: every session runs the default provider and model from `settings.json`, and `/preset` reports "No presets defined". A preset that should be read-only achieves it by *construction* — it removes `edit` and `write` from its `tools` list rather than instructing the model not to use them.

## Modes

Session modes, all off or neutral at start and all toggles — running the command again turns the mode off, or pass an explicit `off`.

| Mode | Toggle | What changes |
|---|---|---|
| Plan | `/plan`, `--plan`, Ctrl+Alt+P | Removes `edit` and `write`, and filters `bash` through a read-only allowlist. Numbered steps from a `Plan:` block are tracked in a status widget; `/steps` lists them. |
| Preset | `/preset`, `--preset`, Ctrl+Shift+U | Swaps model, thinking level, tool set and instructions — see [Presets](#presets). |
| Approve | `/approve` | Confirms every `write` and `edit` before it runs. |
| Approve-all | `/approve-all` | Confirms every tool except `read`, `grep`, `find`, `ls`, `todo` and `questionnaire`. |
| Tool selection | `/tools` | Interactive checklist over the active tool set. Persists to the session, so a stale selection can override `defaultTools` on resume. |

Plan mode, presets and `/tools` all drive the same active tool set, so use one at a time. The approve modes are a separate axis: they gate calls rather than removing tools, and they stay quiet when a guard is already going to block or ask about the same call, so turning one on can only add confirmations.

Together the modes cover three different controls. Plan mode **prevents** by removing tools outright; the approve modes **confirm** at the moment of use; `/rewind` **undoes** after the fact. Note that both approve modes need a UI to ask through — under `-p` a gated call blocks instead, and the mode is restored from the session, so a resumed `/approve-all` session blocks every gated call.

## Guard policy

`guard-rules.json` is data; the extensions that enforce it are the mechanism. Lookup is per cwd, first hit wins: `<cwd>/.pi/guard-rules.json`, then this file.

| Class | Effect | What it covers here |
|---|---|---|
| `zeroAccessPaths` | No read, no write, no bash reference | `.env*`, `secrets.*`, `credentials.*`, `*.pem`, `*.p12`, `~/.ssh`, `~/.aws`, `~/.gnupg`, `~/.netrc`, git credentials |
| `zeroAccessAllowPaths` | Exceptions to the above | `.env.example`, `.env-example`, `.env.template`, `.env.sample` |
| `readOnlyPaths` | Reads fine; writes refused | `.git/`, lockfiles (`poetry.lock`, `package-lock.json`, `Cargo.lock`), `dist/`, `build/`, `/etc` `/usr` `/bin` `/sbin`, shell rc and history files |
| `noDeletePaths` | Deletion and move-away refused | `.git/`, `.github/`, `Dockerfile`, `docker-compose.yml` |
| `bashPatterns` | Regexes over the command string | Destructive `rm`, `sudo`, `chmod 777`; history-rewriting and work-discarding git; unqualified SQL `DROP` / `TRUNCATE` / `DELETE`; `curl \| sh`; `mkfs`; `dd of=/dev/` |

Severity belongs to the rule, not to the extension enforcing it: `ask: true` prompts for confirmation, its absence blocks outright. That is how `git reset --hard` can confirm while `git filter-branch` refuses, from one list. Path classes have no per-rule `ask` — severity is fixed per class. A missing or malformed policy falls back to a `SAFETY_FLOOR` in `extensions/shared/rules.ts` rather than to no protection.

These are speed bumps, not a security boundary. Indirection through `sh -c` or `python -c` defeats path matching, and secrets held in **environment variables** cannot be protected at all — `bash` inherits the process environment. See [Known gaps](extensions/README.md#guards).

## Subagents

`subagent` reads role definitions from `~/.pi/agent/agents/*.md` (user scope) and the nearest `.pi/agents/` directory up the tree (project scope), with `user` the default. No `agents/` directory exists, so no roles are defined: the `scout` and `reviewer` roles [`AGENTS.md`](#agentsmd) describes are not on disk, and every delegation is rejected with `Unknown agent`.

A role is a Markdown file with `name` and `description` frontmatter, optional `tools` and `model`, and a system-prompt body. Three constraints are worth planning around once roles exist: `tools` becomes a strict allowlist for the child, so a role without `bash` cannot run commands and a role without `subagent` cannot delegate further; a child cannot see the parent conversation and the parent cannot see the child's, so each task must be self-contained; and a `model:` string is passed to the child as `--model` and needs the provider prefix (`provider/model`). The agent name must match a defined role exactly, since an unknown name is rejected rather than guessed at.

## AGENTS.md

Prepended to every request, which is why it is kept short. It carries the one thing Pi's default system prompt does not: that `todo`, `questionnaire` and `subagent` exist, and when to reach for them. A model that is not told about a tool will not call it.

`defaultTools` in `settings.json` is the initial active set — `read`, `bash`, `edit`, `write`, `grep`, `find`, `ls`, `todo`, `questionnaire`, `subagent` — and lists all three, so `AGENTS.md` holds true in a session with no preset. Registering a tool is not the same as activating it.

## Extensions

Twenty-one extensions load from `extensions/`, plus one npm package installed via `packages` in `settings.json`.

| Group | Extensions | Adds |
|---|---|---|
| Guards | `permission-gate`, `protected-paths`, `protected-paths-bash`, `approve-gate` | `/approve`, `/approve-all` |
| Tools | `built-in-tool-renderer`, `todo`, `questionnaire` | tools `todo` `questionnaire`; `/todos`, `/read-log` |
| Workflow | `preset`, `plan-mode/`, `tools`, `handoff`, `commands`, `subagent/` | tool `subagent`; `/preset`, `/plan`, `/steps`, `/tools`, `/handoff`, `/commands` |
| Display | `custom-footer`, `notify`, `system-prompt-header` | `/footer` |
| Context | `claude-rules`, `rules-loader`, `shake` | `/shake`, `/unshake` |
| Session | `session-name`, `bookmark` | `/session-name`, `/bookmark`, `/unbookmark` |
| npm | `pi-rewind` 0.5.0 | `/rewind`, Esc Esc |

Mechanism, per-request token cost, known gaps, local modifications and extension interactions are in [`extensions/README.md`](extensions/README.md).
