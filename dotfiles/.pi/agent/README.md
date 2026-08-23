# Pi Agent Configuration

The global Pi configuration, deployed to `~/.pi/agent/`. Everything here applies to every session in every directory.

Project-level files layer on top rather than replacing this: a repo's `AGENTS.md` / `CLAUDE.md` adds to [`AGENTS.md`](#agentsmd), and `<cwd>/.pi/guard-rules.json` is consulted before [`guard-rules.json`](#guard-policy).

## Layout

| Path | What it configures |
|---|---|
| `settings.json` | Provider, default model, default tool set, npm packages, TUI |
| `models.json` | Per-provider overrides — OpenRouter routing only |
| `presets.json` | The `dsv4-flash` → `dsv4-pro` → `review` mode ladder |
| `guard-rules.json` | Path and bash-command policy the guard extensions enforce |
| `AGENTS.md` | Prepended to every request; describes the extension tools and the subagent roles |
| `agents/` | `scout` and `reviewer` subagent role definitions |
| `extensions/` | 21 local extensions plus shared modules — see [`extensions/README.md`](extensions/README.md) |

## Models and providers

The default provider, model and `thinkingLevel` live in `settings.json` and change often — read them there rather than assuming.

`models.json` carries one thing: OpenRouter routing pinned to `data_collection: deny` and `zdr: true`. That is a privacy floor for every request regardless of which model is selected, and it is kept separate from `settings.json` because it is provider policy rather than a preference. `enableInstallTelemetry` is off.

## Presets

The operating model of this config: pick the cheapest tier that can actually do the job, and move up deliberately. `/preset` switches (`preset.ts`).

| Preset | Tier | Thinking | Tools | For |
|---|---|---|---|---|
| `dsv4-flash` | cheap | xhigh | full set | Default working mode. Grep and read targeted ranges rather than whole files; delegate wide recon to `scout` so its summary, not the files, lands in context. |
| `dsv4-pro` | capable | xhigh | full set | Subtle bugs, unclear requirements, design decisions with consequences. Materially more expensive per token, so hand mechanical follow-up back down. |
| `review` | capable | xhigh | **no `edit`/`write`** | Report findings, do not fix them. Correctness → security → reliability, with file and line for every finding. |

Which provider and model each tier resolves to is in `presets.json` — read it there rather than assuming, since the models change.

A preset's `instructions` are appended to the system prompt while it is active, so they cost tokens only then. `review` is read-only by *construction* — it removes `edit` and `write` from the tool set rather than instructing the model not to use them.

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

Together the modes cover three different controls. Plan mode and the `review` preset **prevent** by removing tools outright; the approve modes **confirm** at the moment of use; `/rewind` **undoes** after the fact. Note that both approve modes need a UI to ask through — under `-p` a gated call blocks instead, and the mode is restored from the session, so a resumed `/approve-all` session blocks every gated call.

## Guard policy

`guard-rules.json` is data; the extensions that enforce it are the mechanism. Lookup is per cwd, first hit wins: `<cwd>/.pi/guard-rules.json`, then this file.

| Class | Effect | What it covers here |
|---|---|---|
| `zeroAccessPaths` | No read, no write, no bash reference | `.env*`, `secrets.*`, `credentials.*`, `*.pem`, `*.p12`, `~/.ssh`, `~/.aws`, `~/.gnupg`, `~/.netrc`, git credentials |
| `zeroAccessAllowPaths` | Exceptions to the above | `.env.example`, `.env-example`, `.env.template`, `.env.sample` |
| `readOnlyPaths` | Reads fine; writes refused | `.git/`, lockfiles, `node_modules/`, venvs, `__pycache__/`, `dist/`, `build/`, `/etc` `/usr` `/bin` `/sbin`, shell rc and history files |
| `noDeletePaths` | Deletion and move-away refused | `.git/`, `.github/`, `.gitignore`, `README.md`, `LICENSE`, `CLAUDE.md`, `AGENTS.md`, `pyproject.toml`, `uv.lock`, `Dockerfile`, `docker-compose.yml` |
| `bashPatterns` | Regexes over the command string | Destructive `rm`, `sudo`, `chmod 777`; history-rewriting and work-discarding git; unqualified SQL `DROP` / `TRUNCATE` / `DELETE`; `curl \| sh`; `mkfs`; `dd of=/dev/` |

Severity belongs to the rule, not to the extension enforcing it: `ask: true` prompts for confirmation, its absence blocks outright. That is how `git reset --hard` can confirm while `git filter-branch` refuses, from one list. Path classes have no per-rule `ask` — severity is fixed per class. A missing or malformed policy falls back to a `SAFETY_FLOOR` in `extensions/shared/rules.ts` rather than to no protection.

These are speed bumps, not a security boundary. Indirection through `sh -c` or `python -c` defeats path matching, and secrets held in **environment variables** cannot be protected at all — `bash` inherits the process environment. See [Known gaps](extensions/README.md#guards).

## Subagents

`subagent` reads role definitions from `agents/*.md`. Two are defined:

| Agent | Tier | Tools | Role |
|---|---|---|---|
| [`scout`](agents/scout.md) | cheap | read, grep, find, ls | Recon — locating code, tracing dependencies. Returns a compressed summary with file and line ranges so the caller never reads the files. |
| [`reviewer`](agents/reviewer.md) | capable | read, grep, find, ls | Review against the correctness → security → reliability priority order, in a fixed output format. |

Both are read-only by design, with three consequences worth planning around:

- No `bash`, so `reviewer` cannot produce its own `git diff` — pass the diff text or the changed file paths in the task.
- No `subagent`, so delegation cannot recurse. Split wide work into parallel tasks from the parent.
- A child cannot see the parent conversation and the parent cannot see the child's, so each task must be self-contained.

Each role pins its own model in its frontmatter, and that `model:` string needs the provider prefix. The agent name must match a file exactly, since an unknown name is rejected rather than guessed at.

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
