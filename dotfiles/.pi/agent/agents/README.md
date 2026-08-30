# Pi Sub-Agents

Nine sub-agent definitions for the Pi coding harness. Pi core ships no sub-agents; this repo bundles its own extension (`dotfiles/.pi/agent/extensions/subagent/`), which `install.py` deploys to `~/.pi/agent/extensions/subagent/` (auto-loaded by pi). The definitions follow current best practices: single responsibility, minimal tool grants, read-only by default, and explicit output contracts.

## How the extension runs agents

Each invocation spawns an isolated `pi` process:

```
pi --mode json -p --no-session [--model <model>] [--tools <tools>] --append-system-prompt <body> "Task: ..."
```

Consequences for the agent files:

- Frontmatter fields the extension reads: `name` and `description` (required strings) and `tools` / `model` (optional). Any other field (e.g. `thinking`, `systemPromptMode`) is ignored.
- `description` is what the parent agent sees when deciding which agent to delegate to — keep it specific about when to use the agent and what it returns.
- The markdown body is appended to pi's built-in system prompt; AGENTS.md context files, skills, and extensions still apply to the sub-agent.
- `model` pins the sub-agent's model, with an optional `:<thinking>` suffix (`off`, `minimal`, `low`, `medium`, `high`, `xhigh`, `max`) to fix its thinking/reasoning level. Without the suffix, a pinned model falls back to `defaultThinkingLevel` from `settings.json`, then pi's built-in default (`medium`). Without a `model` field, the sub-agent inherits the dispatching session's model and thinking level. There is no dedicated `thinking` frontmatter field — the extension ignores it.
- `tools` is a strict allowlist over built-in, extension, and custom tools. Names that aren't registered are silently ignored (they do not cause an error).
- Agents run in the dispatching session's working directory (or an explicit `cwd` per task) with the user's full permissions.

## Install

- User scope (all projects): `~/.pi/agent/agents/` — what this repo deploys.
- Project scope: `.pi/agents/` from the project root. Project agents override user agents on name conflicts, and pi asks for confirmation before first use in an untrusted repo.

## Agents

| Agent | Tools | Writes? | Purpose |
|---|---|---|---|
| scout | read, grep, find, ls | No | Codebase recon → compact map |
| docs-researcher | read, grep, find, ls | No | External/API research brief (needs web tools) |
| planner | read, grep, find, ls | No | Minimal numbered implementation plan |
| engineer | read, grep, find, ls, bash, edit, write | Yes | Implements a plan/task: writes code, runs tests |
| test-runner | read, grep, find, ls, bash | No (runs cmds) | Run tests/build, structured triage |
| debugger | read, grep, find, ls, bash, edit | Yes (existing files only) | Reproduce → isolate → fix one bug |
| reviewer | read, grep, find, ls, bash | No | Independent severity-ranked review |
| security-auditor | read, grep, find, ls, bash | No | Vulnerability audit with attack scenarios |
| pr-summarizer | read, grep, find, ls, bash | No | PR/commit summary from git diff |

`scout`, `docs-researcher`, `test-runner`, and `pr-summarizer` pin `openrouter/z-ai/glm-5.3-flash:low` (cheap/fast, low thinking); `engineer` pins `openrouter/z-ai/glm-5.3-flash:max` (cheap model, maximum thinking effort); `planner`, `debugger`, `reviewer`, and `security-auditor` pin `openrouter/z-ai/glm-5.3:high` (stronger reasoning, thinking pinned high). Both models resolve via `pi --list-models`. Remove the `model:` field to inherit the session model and thinking level instead.

## Notes

- `web_search`/`web_fetch` are not pi built-ins and no web-access extension is installed in this setup, so docs-researcher grants only read/grep/find/ls. A comment in `docs-researcher.md` marks where to re-add the web tools once a web extension is available (unregistered tool names would be silently ignored).
- Pi runs with your full user permissions and no built-in approval prompts — sandbox (container/micro-VM) before trusting write-capable agents (debugger) or bash.
- Note the agent files are not yet covered by the `.pi/agent` scope in `dotfiles.yaml`, so `sync_dotfiles.py` reports them as orphaned repo files.
- Recommended chain: scout → planner → implement in main session (or delegate a concrete plan to engineer) → test-runner → reviewer.
