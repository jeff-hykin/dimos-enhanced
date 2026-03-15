# PR-able Review Skill

We are trying to make sure this branch is high quality and ready to be merged into `dev`. Follow these steps in order:

## Step 1: Understand the current branch

1.Try to pull in the latest dev (`git pull origin dev`). If there are conflicts, resolve them in a smart way and commit the changes.

2. If you don't already fully understand this feature branch (if its not in your context) then do the following:
- Collect the diff of this branch as it would appear in a PR against `dev`. This requires fetching the latest `origin/dev` and diffing from the merge-base:

```bash
git fetch origin dev --quiet
git diff $(git merge-base origin/dev HEAD)..HEAD
```

- Also check for any uncommitted local changes:

```bash
git diff
git diff --cached
```

Use that to understand what feature and possible side effects this branch is working on.

## Step 2: Sanity Check the Branch

Run `bin/ci-check` on the repo. If anything fails fix it, but check for auto-changed files and stage those fixes. If there are any relevant/obvious (but selective) tests to run, run them and make sure they pass. If they don't, then fix them. 

## Step 3: Critical code review

Perform a thorough, critical review of ALL changes from Step 1. Evaluate:

- Correctness: logic errors, off-by-one, race conditions, null/None handling
- Security: injection, credentials, unsafe operations
- Performance: unnecessary allocations, O(n^2) where O(n) is possible, missing caching
- Style & consistency: naming, patterns inconsistent with surrounding code
- Tests: missing test coverage for new/changed behavior
- Documentation: public API changes without docstring updates
- Error handling: swallowed exceptions, missing edge cases
- Dependencies: unnecessary new deps, version issues

## Step 4: Present the rating and findings

Output a structured report:

```
## PR-able Rating: X/10

### Problems Found

| # | Problem | Severity | File(s) |
|---|---------|----------|---------|
| 1 | description | critical/high/medium/low | file:line |
| 2 | ... | ... | ... |
```

Then present a structured pick-many question:

```
Which issues would you like me to fix? 

[ ] 1. <problem 1>
[ ] 2. <problem 2>
[ ] 3. <problem 3>
[ ] 4. <problem 4>
...
```

Use the AskUserQuestion tool to get the user's selection.

## Step 5: Fix selected issues

For each issue the user selected:
1. Make the fix
2. Run the most relevant tests for that fix (e.g. if fixing `dimos/core/worker.py`, run tests in `tests/core/` or related test files)
3. If tests fail, debug and iterate until they pass

After all fixes are applied, run `bin/ci-fast` which will both re-run basic checks as well as the testing suite. Keep running and debugging until it passes.

## Step 6: Status report

Present a final summary:

```
## Fix Summary

| # | Problem | Status |
|---|---------|--------|
| 1 | description | Fixed / Fixed (with caveats) / Could not fix |

### Remaining Issues
- Any unselected issues still outstanding

### Updated PR-able Rating: X/10
```


## Step 7: Template

Then minimally fill out the following template and open the filled-out version. Make sure the file is git-ignored or put in /tmp

```
## Problem

<!-- What feature are you adding, or what is broken/missing/sub-optimal? -->
<!-- Context, symptoms, motivation. Link the issue. -->

## Solution

<!-- What you changed and why this approach -->
<!-- Key design decisions / tradeoffs -->
<!-- Keep it high-signal; deep planning belongs in the issue. -->

## Breaking Changes

<!-- Write "None" if not applicable -->

<!-- If applicable:
- what breaks
- who is affected
- migration steps
-->

## How to Test

<!-- This should be command line commands assuming all normal dimos pre-reqs are installed -->

## Contributor License Agreement

- [ ] I have read and approved the [CLA](https://github.com/dimensionalOS/dimos/blob/main/CLA.md).
```