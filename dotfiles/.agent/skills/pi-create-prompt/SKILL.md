---
name: pi-create-prompt
description: Guides authoring Pi prompt templates — Markdown files in prompts/ that expand via /name with argument interpolation. Use when explicitly asked to create or fix a Pi prompt template or /name command. Not for multi-step skills (pi-create-skill) or TypeScript commands (pi-create-extension).
disable-model-invocation: true
---

# pi-create-prompt

A prompt template is a Markdown snippet that `/name` expands into editable prompt text in the user's editor: the model only ever sees the expanded result, never the `/name` invocation, so the body must interpolate every argument and read like a prompt a human might have typed.

Trailing input after `/skill:pi-create-prompt` describes the template to create (task, arguments) or names an existing template to review or fix; with no input, derive the requirements from the conversation and ask for anything missing in one consolidated question.

## Confirm the genre

- Reusable prompt text the user expands, reviews, and edits before sending — a one-shot task or checklist with no bundled files — is a prompt template; continue here.
- Instructions, multi-step workflows, domain knowledge, bundled scripts, or reference docs the agent loads when a task matches belong in a skill: switch to `/skill:pi-create-skill`.
- Behavior instructions cannot express — new tools, slash commands that execute code, event interception, UI — is an extension: switch to `/skill:pi-create-extension`.
- Tiebreak for "/name command" requests: a /name that inserts editable prompt text is a template; a /name that executes code or opens UI is an extension command.
- Don't cram a full workflow with validation loops into a template; write a skill and, if useful, a thin template that invokes it.

## Requirements and naming

- Establish the task, the arguments (required, optional, defaults), and the target directory: global `~/.pi/agent/prompts/`, project `.pi/prompts/` (loaded only after the project is trusted), or a package's `prompts/` directory.
- Filename = command name: `review.md` → `/review`; short, descriptive, verb-like — the filename is the entire trigger.
- Check collisions before naming: extension commands and Pi built-ins shadow same-named templates, and global/project/package scopes collide silently — keep names distinct or namespaced (`team-review.md`).
- Discovery is non-recursive: the file must sit directly in a discovered `prompts/` directory, never in a subdirectory.

## Format

```markdown
---
description: Review staged git changes
argument-hint: "[focus-area]"
---
Review the staged changes (`git diff --cached`). Focus on:
- Bugs and logic errors
- Security issues
- Error handling gaps
${1:+Pay special attention to: $1}
```

- `description`: one short line stating what the command does, shown in the autocomplete dropdown; if missing, the first non-empty body line is used instead, so never leave both unclear.
- `argument-hint`: `<angle brackets>` for required args, `[square brackets]` for optional ones; always set it when the template takes arguments.
- Core Pi recognizes only these two frontmatter fields; don't use extension-added fields unless the target environment has that extension installed.

## Arguments

- `$1`, `$2`, ... — positional; `$@` or `$ARGUMENTS` — all args joined; `${1:-default}` — arg or default; `${@:-default}`; `${@:N}` — args from position N; `${@:N:L}` — L args starting at N.
- Every accepted argument must be interpolated in the body or it is silently dropped — the model never sees it; this is the most common real-world template bug.
- Label interpolations so the expansion stays clear with empty values: "The component name is: $1", not a bare `$1` floating mid-sentence.
- Prefer `${1:-default}` defaults over requiring every argument, and prefer one flexible template over many near-duplicates.
- When all args are free-form instructions, a single labeled `$@` ("Additional instructions: ${@:-none}") is the simplest robust pattern.

## Body rules

- Focused, not generic: one template per specific task — a vague `/help-me` template adds nothing over typing.
- Self-contained: include the commands to run, what to focus on, and the expected output format, since the model gets only the expanded text.
- Concise and imperative: templates are snippets, not documents — state the task, constraints, and output format, and skip what the model already knows.

## Validation

Run until a full pass is clean; any failure means fix, then repeat.

1. Simulate the expansion textually with zero, some, and all arguments, and read each result as a standalone prompt — every variant must be coherent, with no dangling fragments from empty args.
2. Confirm placement directly in a discovered `prompts/` directory, and for a project template that the project is trusted.
3. Walk the checklist:
   - [ ] Filename is short, descriptive, and reads well as `/name`, with no command or scope collision
   - [ ] `description` present, one line
   - [ ] `argument-hint` set if the template takes arguments
   - [ ] Every accepted argument interpolated, labeled, with defaults where sensible
   - [ ] Body self-contained: task, commands, constraints, output format
   - [ ] Task is snippet-sized; workflows moved to a skill
4. Suggest the user confirm `/name` appears in autocomplete and expands as expected.

## Report

State the file path, the `/name` command, the argument-hint, and one example invocation with its expansion.
