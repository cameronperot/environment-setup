---
name: gh-pr-create
description: Creates GitHub pull requests with the gh CLI — branch checks, push, conventional-commit title, structured body. Use when explicitly asked to create or open a PR (including drafts) or push a branch and open a PR.
disable-model-invocation: true
---

# Creating GitHub Pull Requests

Open a pull request with the `gh` CLI. Reviewers read a PR message to decide how to approach the diff, not as a substitute for reading it, so every sentence must earn its place: direct, concise, and specific.

Trailing input after `/skill:gh-pr-create` is a hint — the desired base branch or title/body guidance; with no input, target the repository's default branch and derive the title and body from the branch's commits.

## 1. Gather state

Run these checks in order before writing anything:

1. `git status` — **if** there are uncommitted changes relevant to the PR, stop and ask the user to commit first; this skill does not commit.
2. `git branch --show-current` — **if** on the default branch, stop and ask the user for a feature branch; never open a PR from the default branch.
3. `gh repo view --json defaultBranchRef -q .defaultBranchRef.name` — this is the base branch unless the user named a different one.
4. `gh pr list --head "$(git branch --show-current)" --state open` — **if** a PR already exists, report its URL and stop; use `gh pr edit` only when the user explicitly asked to update it.
5. `git log <base>..HEAD --oneline` and `git diff <base>...HEAD` — review the entire changeset. The PR merges every commit on the branch, so the message must cover all of them, not just the latest commit. **If** the log is empty, there is nothing to open a PR for; stop and say so.

## 2. Push

`git push -u origin HEAD` — only when the branch has no upstream or has local commits the remote lacks.

## 3. Title

Format: `type(scope): subject` — imperative mood, lowercase subject, no trailing period, ≤72 characters. Scope is optional; use the scope the branch's commits share when they have one. Types are the same set as commit headers:

| Type | Use for |
|---|---|
| `feat` | New user-facing capability |
| `fix` | Bug fix |
| `refactor` | Code change that alters neither behavior nor interface |
| `perf` | Performance improvement |
| `docs` | Documentation only |
| `test` | Adding or fixing tests |
| `build` | Build system or dependencies |
| `ci` | CI configuration |
| `chore` | Maintenance that fits none of the above |

Specific enough to identify the change in a list of merged PRs: `fix(orders): prevent double-fill on partial cancel`, not `fix: bug fix`.

## 4. Body

**If** `.github/PULL_REQUEST_TEMPLATE.md` exists in the repo, fill its sections concisely and delete sections that do not apply. **Otherwise** use exactly this structure:

```markdown
## Summary

<1–3 sentences: what changed and why. Lead with the why when it is not obvious from the diff.>

## Changes

- <one bullet per logical change, naming the key files or symbols>

## Testing

<exact commands run and their results, or "Not tested" plus the reason>
```

Style rules:

- Scale to the diff: a trivial PR gets a one-sentence Summary, one Changes bullet, one Testing line.
- Do not restate the diff file-by-file; describe intent and grouping — the diff shows the rest.
- No empty sections, no boilerplate, no filler adjectives ("comprehensive", "robust"), no emoji.
- No AI attribution, generated-by footers, or co-author trailers.
- Report only tests that were actually run, with their actual results.

Good:

```markdown
feat: add rate limiter to order gateway

## Summary

Caps outbound order submissions at the exchange's documented 10 req/s to prevent 429 bans during bursts.

## Changes

- Token-bucket limiter in `gateway/rate_limit.py`
- Applied to `submit_order` and `cancel_order` paths

## Testing

`uv run pytest tests/gateway/` passes; burst replay against the sandbox exchange stayed under the limit.
```

Bad — padded, vague, restates the diff, unverifiable claims:

```markdown
feat: comprehensive rate limiting improvements

## Summary

This PR introduces a comprehensive and robust rate limiting solution to significantly improve the reliability of our trading infrastructure. Modified gateway/rate_limit.py to add a new class, modified gateway/client.py to import it, updated tests.

## Testing

All tests pass. ✅
```

## 5. Create

Use a heredoc so the body's formatting survives the shell:

```bash
gh pr create --title "<title>" --body "$(cat <<'EOF'
<body>
EOF
)"
```

- Add `--base <branch>` only when the base is not the default branch.
- Add `--draft` only when the user asked for a draft.
- Print the URL returned by `gh pr create` as the final output.

## Edge cases

| Situation | Action |
|---|---|
| No commits ahead of base | Stop — nothing to open a PR for |
| Working from a fork | Add `--repo <upstream-owner>/<repo>` and `--head <fork-owner>:<branch>` |
| Push rejected or auth failure | Report the exact error and stop; do not retry blindly |
