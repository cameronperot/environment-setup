---
name: git-review
description: Reviews local git changes (staged, unstaged, or a single commit) offline and reports severity-ranked findings to the terminal; never touches GitHub or modifies the repo. Use when explicitly asked to review the diff, working-tree changes, or a commit before committing or pushing. Not for GitHub PRs (gh-pr-review).
disable-model-invocation: true
---

# git-review

Review local git changes end to end: resolve the scope, gather the diff, read the change in full-file context from the correct git source, verify every finding, and report severity-ranked findings to the terminal. Everything runs locally with read-only git commands (`status`, `diff`, `show`, `rev-parse`); the skill never posts anywhere and never modifies the repo or the index.

## Arguments

If `git rev-parse --is-inside-work-tree` fails, say so and stop.

Trailing input after `/skill:git-review` selects the mode:

1. `staged` (also `cached` or `index`) → staged mode.
2. `unstaged` (also `working` or `working-tree`) → unstaged mode.
3. Anything else → commit mode on that selector; validate it with `git rev-parse --verify --quiet <arg>^{commit}`, and if validation fails, report the invalid selector and stop.

With no input, infer the mode from the request: "the last commit" or a revision named in prose → commit mode; "before I commit" or "what's staged" → staged; "uncommitted" or "working tree" → unstaged. If still ambiguous, resolve from repo state with `git status --porcelain=v1 -uall`: any entry staged for commit (first status column not a space or `?`) → staged; otherwise any working-tree edit or `??` untracked entry → unstaged; otherwise commit mode on HEAD.

Always announce the resolved mode in the report header so a wrong guess costs the user one word to correct; never silently review the wrong thing. To review staged and unstaged changes together when asked, diff with `git diff HEAD`, add untracked files, and apply both context rules below.

## Workflow

### 1. Gather the diff

**Staged.** Run `git diff --staged`. Read full-file context for changed files from the index with `git show :<path>`, not from the working tree: when a file has both staged and unstaged edits, the working tree does not match what will be committed, so a working-tree read reviews code that is not under review. Pipe through `nl -ba` when line numbers are needed; plain `nl` skips blank lines and misnumbers anchors.

**Unstaged.** Run `git diff`. This misses untracked files entirely: collect the `??` entries from `git status --porcelain=v1 -uall` and review each as a wholly-new file read from the working tree. The `-uall` flag matters — without it an untracked directory collapses to a single `dir/` entry that hides every file inside. Working-tree files are exactly the content under review; read them normally.

**Commit.** Default to HEAD; accept any commit-ish. Run `git show <sha>` to get the message and diff together. Read full-file context at that commit with `git show <sha>:<path>` — the working tree may be dirty or HEAD may have moved on; only when reviewing HEAD with a clean tree are working-tree reads equivalent. A root commit needs no special handling with `git show` (it diffs against the empty tree); never construct `<sha>^`, which does not exist for a root commit. Detect a merge commit by parent count from `git show -s --format=%P <sha>`: `git show` on a merge prints a combined diff that is usually empty for a clean merge, so review the first-parent diff `git diff <sha>^1 <sha>` and say in the report that the merge is reviewed against its first parent.

### 2. Understand intent before reading code

Review the change against its purpose, not against what you would have built. In commit mode the commit message states the intent and is itself under review: flag a message that does not match the change, and flag scope creep relative to it. Staged and unstaged changes have no written intent: infer it from the conversation (the changes were usually just made in this session), state the inferred intent in the report header so the user can correct it, and ask first only when the change is large and the intent is not inferable.

### 3. Read the diff with surrounding context

Never judge hunks in isolation — a diff hides the code around it. Read changed files in full from the mode's context source above. Trace callers of changed functions across the repo (the whole repo is local — search it directly) to catch missed call sites and broken contracts; the most common review miss is a caller the diff never touched.

### 4. Review passes in priority order

Make one pass per dimension, most important first. Time spent on style is wasted if the logic is wrong.

| Priority | Dimension | What to look for |
|---|---|---|
| 1 | Correctness | Logic errors, unhandled edge cases, off-by-one, inverted conditionals, broken invariants, race conditions |
| 2 | Security | Injection, secrets in the diff, authz/authn gaps, unsafe deserialization, suspicious dependency changes |
| 3 | Reliability | Missing error handling, resource leaks, failure paths, backwards compatibility of APIs, contracts, and migrations |
| 4 | Performance | Only real, measurable issues on hot paths — no speculative micro-optimization nits |
| 5 | Tests | New behavior has tests, tests assert the behavior rather than just executing the code, edge cases covered |
| 6 | Style/docs | Only what linters cannot enforce; skip anything CI already checks |

Staged and unstaged review runs before the change enters history, so a secret caught here is removed with an edit instead of a history scrub — treat any credential in the diff as a blocker.

### 5. Verify every finding

Before reporting a finding, re-read the actual code and construct a concrete failure scenario: which inputs or state lead to which wrong outcome. Drop findings that are speculative or that the surrounding code already handles. This step is the main lever against false positives — an unverified finding costs the author more time than it saves.

### 6. Report

Open with a header naming the resolved mode and scope, e.g. `## Review: staged changes (3 files, +120 −41)` or `## Review: commit abc1234 — "Add retry logic"`, plus the inferred-intent line for staged or unstaged mode. Then a verdict with a one-sentence rationale: `ready to commit`, `needs work`, or `comments only` for staged/unstaged; `looks good` or `needs follow-up` for commit mode. Suggest `git commit --amend` as the remedy only when the reviewed commit is HEAD and unpushed; otherwise suggest a follow-up commit.

Rank findings by severity. Severity tags: `[blocker]` must be fixed before the change ships, `[should-fix]` should be fixed but is not blocking, `[question]` needs the author's input, `[nit]` author's discretion. Anchor every finding to `file:line` using new-side line numbers (the version under review); for a pure deletion, cite the old line and note that it was removed. State the defect in one sentence, give the failure scenario, and suggest a fix. Phrase uncertain findings as questions. Comment on the code, never the author, and explain why, not just what.

Write every finding as directly and concisely as possible — vague or padded feedback wastes the author's time and buries the defect. Lead with the defect, one finding per item, short declarative sentences. Cut every word that does not change what the author does next: no hedging ("maybe", "I think", "it might be worth"), no softeners or apologies ("just a small thing", "sorry to nitpick"), no praise padding before criticism, no restating what the diff already shows, no sign-offs.

Example report:

```
## Review: staged changes (2 files, +58 −4)

Intent (inferred): add retry logic to order submission.

Verdict: needs work — the retry loop can submit a duplicate order (finding 1).

1. [blocker] src/orders.py:87 — the retry loop resubmits without re-checking order state.
   If the first submission succeeds but the ACK times out, the retry creates a duplicate order.
   Fix: query order status before each retry and abort if the order already exists.
2. [should-fix] src/orders.py:102 — `max_retries` from config is unvalidated; a value of 0 skips submission entirely and still returns success.
3. [question] tests/test_orders.py:55 — the test asserts the retry count but not the payload; is an identical payload across retries intentional?
4. [nit] src/orders.py:79 — `retrys` → `retries`.
```
