# PR-able Review Skill

Follow these steps in order:

## Step 1: Run pre-commit checks

Run `pre-commit run --all-files` on the repo. If any hooks fail and auto-fix files, stage those fixes. If hooks still fail after auto-fix, note the failures for the review.

## Step 2: Gather all changes against dev

Collect the full diff of all changes (unstaged, staged, and committed) compared to the `dev` branch:

```
git diff dev...HEAD
git diff dev
git diff --cached
```

Combine these to understand the complete set of changes that would go into a PR against `dev`.

## Step 3: Critical code review

Perform a thorough, critical review of ALL changes from Step 2. Evaluate:

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

After all fixes are applied, run `pre-commit run --all-files` one final time to ensure everything is clean.

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
