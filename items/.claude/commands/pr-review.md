# PR Review & Validation

Review the current branch for PR readiness. This command runs validation, performs a code review (optionally as Paul), and helps fix issues.

## Step 1: Understand the current branch

1. Try to pull in the latest dev (`git pull origin dev`). If there are conflicts, resolve them intelligently and commit.

2. Collect the diff of this branch against `dev`:

```bash
git fetch origin dev --quiet
git diff $(git merge-base origin/dev HEAD)..HEAD
```

Also check for uncommitted changes:

```bash
git diff
git diff --cached
```

## Step 2: Sanity Check

Run `bin/ci-check` on the repo. If anything fails, fix it — but check for auto-changed files and stage those fixes. If there are relevant/obvious tests to run, run them.

Be EXTREMELY SKEPTICAL of "pre-existing failures". If there is a pre-existing failure, that is a HUGE deal — figure out exactly why before continuing.

## Step 3: Paul Review (sub-agent)

Spawn a sub-agent using the Agent tool to perform a Paul Nechifor-style code review. Use the following prompt for the sub-agent:

---

You are Paul Nechifor, a senior developer at Dimensional. You are performing a code review.

### Your review personality

- Thorough, precise reviews that catch real issues
- Direct communication — state what needs to change clearly
- Provide code suggestions when the fix is obvious
- Ask probing questions when intent is unclear
- Care deeply about code quality, error handling, and correctness
- Don't nitpick style when there are bigger issues

### Your review approach

Start from the entrypoint (most often blueprints). Sometimes review code in unconventional order — less context is good because debugging often gives you less context and code should still make sense.

For each class or function ask:
- Is this combining too many unrelated things?
- Is this code efficient?
- Is it thread safe? Does it have to be?
- Is all contextual data stored properly and cleaned up?
- Is any of the code unnecessary?
- Is the code hard to understand (cyclomatic complexity)?
- Does it handle errors properly?
- Is it tested?

### Reference materials

Read `_help/paul_review/patterns.md` for Paul's historical review patterns. Use `_help/paul_review/comments.json` as a reference database if you need specific examples of how Paul comments.

### Output format

For each issue found:

### [file_path]:[line_range]

**Severity:** must-fix | should-fix | nit
**Category:** Code Style | Architecture | Error Handling | Performance | Type Safety | Testing | etc.

[Description of the issue and suggested fix]

---

Provide the sub-agent with the full diff from Step 1.

## Step 4: Critical code review (your own)

In addition to the Paul review, perform your own review evaluating:

- Correctness: logic errors, off-by-one, race conditions, null/None handling
- Security: injection, credentials, unsafe operations
- Performance: unnecessary allocations, O(n^2) where O(n) possible
- Style & consistency: naming, patterns inconsistent with surrounding code
- Tests: missing coverage for new/changed behavior
- Error handling: swallowed exceptions, missing edge cases
- Dependencies: unnecessary new deps

## Step 5: Present findings

Combine both reviews. Output a structured report:

```
## PR-able Rating: X/10

### Problems Found

| # | Source | Problem | Severity | File(s) |
|---|--------|---------|----------|---------|
| 1 | Paul   | desc    | must-fix | file:line |
| 2 | Review | desc    | should-fix | file:line |
```

Then present a pick-many question using AskUserQuestion:

```
Which issues would you like me to fix?

[ ] 1. <problem 1>
[ ] 2. <problem 2>
...
```

## Step 6: Fix selected issues

For each selected issue:
1. Make the fix
2. Run `ruff check --fix && ruff format`
3. Run the most relevant tests
4. If tests fail, debug and iterate

After all fixes, run `bin/ci-fast`. Keep iterating until it passes.

## Step 7: Status report

```
## Fix Summary

| # | Problem | Status |
|---|---------|--------|
| 1 | desc    | Fixed / Fixed (with caveats) / Could not fix |

### Remaining Issues
- Any unselected issues still outstanding

### Updated PR-able Rating: X/10
```

## Step 8: PR Template

Fill out the PR template and save to `/tmp/pr-description.md`:

```
## Problem
<!-- What feature/fix -->

## Solution
<!-- What changed and why -->

## Breaking Changes
<!-- None, or list them -->

## How to Test
<!-- Reproducible commands -->

## Contributor License Agreement
- [ ] I have read and approved the [CLA](https://github.com/dimensionalOS/dimos/blob/main/CLA.md).
```
