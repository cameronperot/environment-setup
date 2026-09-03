---
name: bash-conventions
description: Shell Style Guide with house defaults for writing, editing, or reviewing Bash scripts and sourced libraries, plus the shfmt/shellcheck/bash -n workflow. Use whenever writing bash scripts.
---

# bash-conventions

Trailing input after `/skill:bash-conventions` names paths, functions, or requirements to apply the conventions to; with no input, apply them to the shell code in the current context.

## Setup

- Debian/Ubuntu: `sudo apt-get install shellcheck shfmt`; verify with `shfmt --version` and `shellcheck --version`.
- Without a shellcheck package, `uv tool install shellcheck-py` provides the same binary.
- Never install unasked; give the user the command and continue with the fallback in the workflow.

## Workflow

1. Write or edit the script; for a new file read `references/templates.md` first, start from the matching skeleton, and delete every flag and helper the script does not need.
2. Format a new file with `shfmt -i 4 -bn -w <file>`. For an existing file run `shfmt -i 4 -bn -d <file>` first and apply `-w` only when the diff is confined to lines you changed; otherwise match the file's existing style and mention the drift, because change discipline forbids reformatting adjacent code.
3. Lint with `shellcheck -x -P SCRIPTDIR -o require-variable-braces,require-double-brackets <file>` and fix root causes, never symptoms. **IF** `command -v shellcheck` fails **THEN** run `bash -n <file>`, tell the user shellcheck is missing and how to install it, and state in the final report that lint did not run; never skip silently.
4. Syntax-check with `bash -n <file>`.
5. Run it: `<file> --help`, then the happy path (`--dry-run` when present, otherwise in a scratch directory), and check the exit status; exercise a library with `bash -c 'source ./lib.sh && lib::fn args'`; trace surprises with `bash -x <file>`.
6. Repeat steps 2–5 until `shfmt -d` prints nothing and shellcheck is clean, then report which checks ran and which were skipped.

Flag rationale:

- `-i 4` is the house indent (Google specifies 2).
- `-bn` keeps `|`, `&&` and `||` at the start of continuation lines; without it shfmt moves them to the end of the line before.
- `-ci` is deliberately absent: house case patterns sit at the `case` indent.
- `-sr` is absent: house redirects are written `>&2` and `2>/dev/null`.
- Add `-ln bash` only for a file with neither a shebang nor a `.sh` extension.
- `-x -P SCRIPTDIR` lets shellcheck follow `source "${SCRIPT_DIR}/lib.sh"`; the two optional checks enforce `"${var}"` braces and `[[ ]]` mechanically.

## Scope

- Use shell only for small utilities and wrapper scripts that mostly call other programs.
- **IF** the script needs more than ~100 lines, non-trivial data manipulation, or performance **THEN** propose a Python rewrite before continuing.
- Executables take a `.sh` extension or none; libraries take `.sh` and are not executable.
- Start executables with `#!/usr/bin/env bash` and put `set -euo pipefail` on the first line after the header comment (house; Google specifies `#!/bin/bash` and only "minimal flags").
- Write for `bash script.sh` invocation: never rely on options passed on the shebang line.

## File Layout

- Order: shebang, header comment, `set -euo pipefail`, constants, mutable globals with defaults, functions, `main()`, the `main` guard.
- Declare constants with `readonly NAME=value`, arrays with `readonly -a`, maps with `declare -rA`.
- Keep every function together below the constants; no executable statements between or after functions except the guard.
- Once a file has any other function, `main()` is required and is the last function.
- End the file with `if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then main "$@"; fi` so the script is sourceable for tests (house; Google uses a bare `main "$@"`).
- Locate sibling files with `SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"` and `source "${SCRIPT_DIR}/lib.sh"`, never relative to the caller's cwd.
- A script that takes flags has `usage()` printing a heredoc that ends with an `Examples:` section; `-h`/`--help` writes it to stdout and exits 0, a usage error writes it to stderr and exits 1.
- A wrapper that hands off to another program ends with `exec` so signals and the exit status pass through.

## Formatting

- Indent 4 spaces, never tabs, except the body of a `<<-` heredoc (house; Google specifies 2).
- Keep lines within 80 columns; break long literals with a heredoc or an embedded newline, never a long unbroken string.
- Split a pipeline or `&&`/`||` chain that does not fit one segment per line, with `\` ending each line and the operator starting the next.
- Put `; then` and `; do` on the opener line; `else`, `fi` and `done` stand alone.
- Keep case patterns at the same indent as `case`, written `-h | --help)` with spaces around `|` (house shfmt default; Google indents them one level).
- Write a one-line alternative as `pattern) command ;;`; otherwise put the pattern, the actions and `;;` on separate lines.
- Do not use `;&` or `;;&`.
- Let shfmt own layout; never hand-align columns.

## Quoting and Expansion

- Quote every variable expansion and command substitution: `"${var}"`, `"$(cmd)"`.
- Brace named variables and leave `$1`, `$#`, `$?`, `$@` unbraced unless braces disambiguate (`"${10}"`, `"${1}0"`).
- Braces are not quoting: an unquoted `${var}` still word-splits and globs.
- Pass arguments on with `"$@"`; use `$*` only to join them into a message.
- Never quote literal integers (`count=0`), and leave variables unquoted inside `(( ))`.
- Expand globs as `./*`, never `*`, because file names may begin with `-`.
- Always `read -r`.
- Store lists and argument vectors in arrays (`declare -a flags=()`, `flags+=(--x)`, `"${flags[@]}"`), never in a space-joined string.
- Use `declare -A` only when a real key-to-value map is needed.
- Prefer parameter expansion (`${0##*/}`, `${path%.sh}`, `${str/#foo/bar}`, `BASH_REMATCH`) over `basename`, `sed`, `awk` or `expr` for simple string work.

## Tests and Arithmetic

- Use `[[ … ]]`, never `[ … ]` or `test`.
- Compare strings with `==`, not `=`; test emptiness with `-z`/`-n`, not filler characters.
- Compare numbers inside `(( … ))`; `<` and `>` inside `[[ ]]` compare lexicographically.
- Compute with `$(( … ))`; never `let`, `expr` or `$[ … ]`.
- Never write a standalone `(( expr ))` whose value can be 0: under `set -e`, `(( i++ ))` with `i=0` exits the shell, so write `i=$(( i + 1 ))` or `(( i += 1 ))`.

## Errors and Exit Status

- Send every error and warning to stderr through `die()` and `warn()` helpers prefixed `${0##*/}: error:` and `${0##*/}: warning:`; never `echo` an error to stdout.
- Check every non-piped command with `if ! cmd; then … fi` or `cmd || die "…"`, including `cd` and `pushd`.
- Capture pipeline statuses on the very next line, `codes=("${PIPESTATUS[@]}")`, because any following command, `[[` included, overwrites them.
- Under `set -u`, read possibly-unset variables as `"${VAR:-}"`.
- Under `pipefail`, append `|| true` only to a command whose non-zero status is expected (`grep` with no match) and say why in a comment.
- Never `2>/dev/null` an error you have not handled.
- Read command output with `while read -r line; do …; done < <(cmd)` or `readarray -t lines < <(cmd)`; piping into `while` runs the loop in a subshell and loses its assignments.
- Separate declaration from a command-substitution assignment, `local out; out="$(cmd)"` and `X="$(cmd)"; readonly X`, because `local`, `readonly`, `declare` and `export` return their own status and mask the command's.
- Make a constant `readonly` on its own line immediately after its (possibly conditional) assignment.

## Functions and Variables

- Declare functions as `name() {` without the `function` keyword (house; Google allows either if consistent).
- Name functions and variables `lower_snake`; reserve `UPPER_SNAKE` for constants and exported variables, declared at the top of the file.
- Namespace library functions `lib::fn`.
- Declare every function variable `local`; Bash scopes dynamically, so callees see a caller's locals.
- Name loop variables after what they iterate (`for zone in "${zones[@]}"`).
- Never assign to Bash special variables (`UID`, `RANDOM`, `LINENO`, `PATH` by accident) or to underscore-prefixed names.
- Use functions, never aliases, in scripts.

## Comments

- The file header states what the file does and, for executables, how to invoke it.
- Any function that is not both short and obvious, and every library function, gets a header block fenced with `#######################################` carrying `Globals:`, `Arguments:`, `Outputs:` and `Returns:` lines; omit lines that do not apply.
- Comment only the non-obvious, explaining why rather than what.
- Write `# shellcheck disable=SCnnnn` only with the reason on the same line, never a blanket disable.

## Script Modes

- Any script with `main()` accepts `--debug`, which runs `set -x`.
- Any script with `main()` that changes state outside its own output also accepts `--dry-run`, which prints the intended actions and touches nothing, and `-v`/`--verbose`, which reports decisions to stderr through `log_verbose()`.
- Short linear scripts without `main()` are exempt.

## Consistency

- When editing an existing file whose style is internally consistent, keep its indent and conventions and mention any drift from this skill rather than reformatting.
- Apply every rule here in full to new files.

## References

- `references/templates.md`: an annotated executable skeleton, a sourceable library skeleton, and wrong/right pairs for the rules above; read it when creating a new script or library, adding argument parsing, usage or logging helpers, or when unsure what a rule looks like in code.
