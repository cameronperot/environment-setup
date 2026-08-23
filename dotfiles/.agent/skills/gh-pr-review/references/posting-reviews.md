# Posting Reviews to GitHub

Mechanics for submitting a review to GitHub after the user has explicitly asked for it. Show the user the findings before posting so they can vet what gets published.

## Review without inline comments

```sh
gh pr review <sel> --approve --body "<summary>"
gh pr review <sel> --request-changes --body "<summary>"
gh pr review <sel> --comment --body "<summary>"
```

## Review with inline comments

`gh pr review` cannot attach inline comments, so use the REST API. Run this sequence exactly.

1. Get the head commit SHA:

```sh
gh pr view <sel> --json headRefOid --jq .headRefOid
```

2. Write the payload to a temporary file (e.g. `payload.json`):

```json
{
  "commit_id": "<head SHA from step 1>",
  "event": "REQUEST_CHANGES",
  "body": "<review summary>",
  "comments": [
    { "path": "src/orders.py", "line": 87, "side": "RIGHT", "body": "<finding>" },
    { "path": "src/orders.py", "start_line": 100, "start_side": "RIGHT", "line": 104, "side": "RIGHT", "body": "<multi-line finding>" }
  ]
}
```

3. Submit in one call (`{owner}` and `{repo}` are resolved by gh from the current repo — pass them verbatim):

```sh
gh api repos/{owner}/{repo}/pulls/<number>/reviews --input payload.json
```

Constraints:

- `event` must be `APPROVE`, `REQUEST_CHANGES`, or `COMMENT`. Always include it: submitting in one call creates and submits the review atomically, while omitting `event` leaves a pending review nobody else can see.
- Each comment's `line` must be a line present in the diff, on the side given by `side` (`RIGHT` = new code, `LEFT` = deleted code). The API rejects the whole review with a 422 otherwise. If a finding's anchor is outside the diff, move that finding into the review `body` instead.
- You cannot `APPROVE` or `REQUEST_CHANGES` on your own PR; use `COMMENT`.

## Suggestion blocks

For a small concrete fix, put a suggestion fence in the inline comment body so the author can apply it with one click. The suggested lines replace exactly the line range the comment is anchored to.

````
```suggestion
retries += 1
```
````

## Verify

```sh
gh pr view <sel> --json reviews --jq '.reviews[-1] | {author: .author.login, state, body}'
```

Confirm the review landed with the intended state. On an API error, report the error verbatim to the user and fix the payload; do not retry blindly.
