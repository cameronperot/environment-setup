# Bash templates

Contents: [Executable script](#executable-script) · [Sourceable library](#sourceable-library) · [Wrong and right](#wrong-and-right)

## Executable script

Start from this skeleton and delete every flag, helper and constant the script does not need; a script too short for `main()` keeps only the header, `set -euo pipefail`, and a linear body.
Comments beginning `rule:` name the convention a line satisfies and do not belong in the real script.

```bash
#!/usr/bin/env bash
#
# sync_backups.sh — copy the backup set to a destination directory.
#
# Usage: sync_backups.sh [-v] [-x PATTERN]... [--dry-run] [--debug] <dest>

set -euo pipefail

# rule: constants first, UPPER_SNAKE, readonly on its own line after a
# runtime assignment so a failing substitution is not masked
BACKUP_ROOT="${BACKUP_ROOT:-${HOME}/backups}"
readonly BACKUP_ROOT
readonly -a RSYNC_FLAGS=(--archive --delete)

# rule: mutable globals declared once, with defaults, before any function
dry_run=0
verbose=0
excludes=()
dest=""

usage() {
    cat <<EOF
Usage: ${0##*/} [options] <dest>

Copy ${BACKUP_ROOT} to <dest>.

Options:
  -h, --help         show this help
  -v, --verbose      report decisions on stderr
  -x, --exclude PAT  skip paths matching PAT (repeatable)
  --dry-run          print the rsync command without running it
  --debug            trace execution (set -x)

Examples:
  ${0##*/} /mnt/backup
  ${0##*/} --dry-run -x '*.tmp' /mnt/backup
EOF
}

die() {
    echo "${0##*/}: error: $*" >&2
    exit 1
}

warn() {
    echo "${0##*/}: warning: $*" >&2
}

log_verbose() {
    if ((verbose)); then
        echo "${0##*/}: $*" >&2
    fi
}

#######################################
# Parse flags and the positional destination.
# Globals: dry_run, verbose, excludes, dest (modified)
# Arguments: the script's "$@"
# Outputs: usage to stdout on -h; usage and errors to stderr on misuse
# Returns: 0, or exits 1 on a usage error
#######################################
parse_args() {
    while (($# > 0)); do
        case "$1" in
        -h | --help)
            usage
            exit 0
            ;;
        -v | --verbose)
            verbose=1
            shift
            ;;
        -x | --exclude)
            (($# >= 2)) || die "$1 needs a value"
            excludes+=(--exclude "$2")
            shift 2
            ;;
        --dry-run)
            dry_run=1
            shift
            ;;
        --debug)
            set -x
            shift
            ;;
        --)
            shift
            break
            ;;
        -*)
            usage >&2
            die "unknown option: $1"
            ;;
        *)
            break
            ;;
        esac
    done
    (($# == 1)) || die "expected exactly one <dest>, got $#"
    dest="$1"
}

#######################################
# Copy the backup root to the destination.
# Globals: BACKUP_ROOT, RSYNC_FLAGS, excludes, dest, dry_run
# Arguments: none
# Outputs: the rsync command to stdout when dry_run is set
# Returns: rsync's exit status; exits 1 when the destination is missing
#######################################
sync_backups() {
    [[ -d "${dest}" ]] || die "destination not found: ${dest}"
    log_verbose "syncing ${BACKUP_ROOT} to ${dest}"
    if ((dry_run)); then
        # rule: $* is right here, the words are joined into a message
        echo "rsync ${RSYNC_FLAGS[*]} ${excludes[*]} ${BACKUP_ROOT}/ ${dest}/"
        return 0
    fi
    # rule: arrays expand into separate arguments with "${arr[@]}"
    rsync "${RSYNC_FLAGS[@]}" "${excludes[@]}" "${BACKUP_ROOT}/" "${dest}/"
}

main() {
    parse_args "$@"
    sync_backups
}

# rule: the guard keeps the file sourceable for tests
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

## Sourceable library

A library is a `.sh` file that is not executable, sets no shell options because the sourcing script owns `set -euo pipefail`, holds only constants and functions, and refuses direct execution.
Keep the shebang so shellcheck and editors know the dialect.

```bash
#!/usr/bin/env bash
#
# log.sh — logging helpers shared by the deployment scripts.
# Source it; do not execute it.

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "${0##*/}: this file is a library; source it instead" >&2
    exit 1
fi

#######################################
# Write a timestamped message to stderr.
# Arguments: message words
# Outputs: the message to stderr
#######################################
log::err() {
    echo "[$(date +'%Y-%m-%dT%H:%M:%S%z')] $*" >&2
}

#######################################
# Write a timestamped message to stderr and exit.
# Arguments: message words
# Outputs: the message to stderr
# Returns: never; exits 1
#######################################
log::die() {
    log::err "$@"
    exit 1
}
```

The consumer locates the library relative to its own path, never the caller's cwd:

```bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_DIR
source "${SCRIPT_DIR}/lib/log.sh"
```

## Wrong and right

| Rule | Wrong | Right |
|---|---|---|
| `local` masks the substitution's exit status | `local out="$(cmd)"` | `local out; out="$(cmd)"` |
| So does `readonly` | `readonly X="$(cmd)"` | `X="$(cmd)"; readonly X` |
| Standalone `(( ))` evaluating to 0 exits under `set -e` | `(( i++ ))` | `i=$(( i + 1 ))` |
| Pipe into `while` loses assignments to a subshell | `cmd \| while read -r l; do n=$l; done` | `while read -r l; do n=$l; done < <(cmd)` |
| `[[ ]]` over `[ ]`, `==` over `=` | `[ "$a" = "$b" ]` | `[[ "${a}" == "${b}" ]]` |
| Brace and quote named variables | `echo $path` | `echo "${path}"` |
| `<`/`>` in `[[ ]]` compare as strings | `[[ $a > $b ]]` | `(( a > b ))` |
| `PIPESTATUS` dies on the next command | `cmd1 \| cmd2; [[ -f x ]]; echo "${PIPESTATUS[1]}"` | `cmd1 \| cmd2; codes=("${PIPESTATUS[@]}")` |
| Continuation operator leads the line | `cmd1 \|\` then `    cmd2` | `cmd1 \` then `    \| cmd2` |
| Globs may expand to `-flags` | `rm -v *` | `rm -v ./*` |
| Errors go to stderr | `echo "failed"; exit 1` | `die "failed"` |
| `"$@"` preserves argument boundaries | `run_it $*` | `run_it "$@"` |
| Builtins over processes | `name="$(basename "$0")"` | `name="${0##*/}"` |
