---
name: gh-pr-review
description: Reviews GitHub pull requests with the gh CLI and reports severity-ranked findings; posts to GitHub only when explicitly asked. Use when explicitly asked to review a PR or leave review comments. Not for local changes without a PR (git-review).
disable-model-invocation: true
---

# GitHub PR Review

Review a pull request end to end: gather context, read the change in context, verify every finding, and report severity-ranked findings. Report in the terminal by default; post to GitHub only when the user explicitly asks.

Trailing input after `/skill:gh-pr-review` selects the PR — a number, full URL, or branch name; with no input, resolve the current branch's PR with `gh pr view`, and if it has none, run `gh pr list` and ask the user which one to review.

## Prerequisites

The `gh` CLI must be installed and authenticated; verify with `gh auth status`. Authentication comes from the user's gh config or the `GH_TOKEN` environment variable — never from this skill.

## Workflow

### 1. Gather context

Run exactly:

```sh
gh pr view <sel> --json number,title,body,author,baseRefName,headRefName,state,isDraft,labels,files,additions,deletions,statusCheckRollup,reviews,comments
gh pr diff <sel>
```

Read any issues linked from the PR body with `gh issue view <n>` to understand the stated intent. Note existing reviews and unresolved comment threads so you don't repeat feedback. Note CI status from `statusCheckRollup`: failing checks are a finding, not a reason to skip the review.

### 2. Understand intent before reading code

Review the change against its stated purpose, not against what you would have built. Flag as findings: scope creep (changes unrelated to the stated purpose) and missing context (no description, no linked issue for a non-trivial change).

### 3. Read the diff with surrounding context

Never judge hunks in isolation — a diff hides the code around it. Read the changed files at the head ref for full context: `git fetch origin <headRefName>` and read from that ref, or `gh pr checkout <sel>` when you need to run or trace the code. Trace callers of changed functions to catch missed call sites and broken contracts; the most common review miss is a caller the diff never touched.

### 4. Review passes in priority order

Make one pass per dimension, most important first. Time spent on style is wasted if the logic is wrong.

| Priority | Dimension | What to look for |
|---|---|---|
| 1 | Correctness | Logic errors, unhandled edge cases, off-by-one, inverted conditionals, broken invariants, race conditions |
| 2 | Security | Injection, secrets committed in the diff, authz/authn gaps, unsafe deserialization, suspicious dependency changes |
| 3 | Reliability | Missing error handling, resource leaks, failure paths, backwards compatibility of APIs, contracts, and migrations |
| 4 | Performance | Only real, measurable issues on hot paths — no speculative micro-optimization nits |
| 5 | Tests | New behavior has tests, tests assert the behavior rather than just executing the code, edge cases covered |
| 6 | Style/docs | Only what linters cannot enforce; skip anything CI already checks |

### 5. Verify every finding

Before reporting a finding, re-read the actual code and construct a concrete failure scenario: which inputs or state lead to which wrong outcome. Drop findings that are speculative or that the surrounding code already handles. This step is the main lever against false positives — an unverified finding costs the author more time than it saves.

### 6. Report

Output a verdict line (approve, request changes, or comment) with a one-sentence rationale, then findings ranked by severity. Severity tags: `[blocker]` must be fixed before merge, `[should-fix]` should be fixed but is not merge-blocking, `[question]` needs the author's input, `[nit]` author's discretion. Anchor every finding to `file:line`, state the defect in one sentence, give the failure scenario, and suggest a fix. Phrase uncertain findings as questions. Comment on the code, never the author, and explain why, not just what.

Write every comment as directly and concisely as possible — vague or padded feedback wastes the author's time and buries the defect. Lead with the defect, one finding per comment, short declarative sentences. Cut every word that does not change what the author does next: no hedging ("maybe", "I think", "it might be worth"), no softeners or apologies ("just a small thing", "sorry to nitpick"), no praise padding before criticism, no restating what the diff already shows, no sign-offs.

Example report:

```
## Review: #142 — Add retry logic to order submission

Verdict: request changes — the retry loop can submit a duplicate order (finding 1).

1. [blocker] src/orders.py:87 — the retry loop resubmits without re-checking order state.
   If the first submission succeeds but the ACK times out, the retry creates a duplicate order.
   Fix: query order status before each retry and abort if the order already exists.
2. [should-fix] src/orders.py:102 — `max_retries` from config is unvalidated; a value of 0 skips submission entirely and still returns success.
3. [question] tests/test_orders.py:55 — the test asserts the retry count but not the payload; is an identical payload across retries intentional?
4. [nit] src/orders.py:79 — `retrys` → `retries`.
```

## Posting the review to GitHub

Only when the user explicitly asks: follow `references/posting-reviews.md`. Never post without an explicit request — a published review is visible to everyone on the PR and cannot be unsent.
