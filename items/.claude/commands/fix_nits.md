# Fix Nits

Fix common style/correctness nits across the files that would be part of a PR review.

## Step 1: Get the files in scope

Get all the files that would be part of a PR review:

```bash
git fetch origin dev --quiet
git diff $(git merge-base origin/dev HEAD)..HEAD
```

## Step 2: Within those files, check the following

- self.<word>._transport, we should basically never use _transport, that usually indicates that a start method forgot to have a `@rpc` decorator
- Use grep to find every `def start` and check all subscribe calls within the body. Every `start` should:
    - have an `@rpc` decorator
    - begin with `super().start()`
    - wrap every `subscribe` with `register_disposable`, e.g.
      `self.register_disposable(Disposable(self.agent.subscribe(self._on_agent_message)))`
- Use grep to find any indented (non-top-level) import statements. If they can be moved to the top of the file without a performance penalty (e.g. `from typing import Any`), move them.
- Use grep to find every `# type: ignore` (and similar typing-ignore comments). Confirm each one is still actually needed; remove the ones that aren't.
- Use LSP tools to check for any dead code in those changes
- if there are magic numbers like `70` or `2.5` or `30` make sure they are in a describptive variable
- Run `tree` on the `docs/` dir and see if there are any docs that need updating based on changes made to the code.
- Read all the docstrings and comments in the changed files. Remove any that are junk/noise. Example of noise to delete:
  ```python
  # create nav stack
  n = create_nav_stack()
  ```
- Grep for all module definitions and make sure there are no `__setstate__` or `__getstate__` methods on modules — they have no purpose and should be removed.
- While doing the above, if any variable names are shortened (e.g. `mod` instead of `module`), expand them to the full word.

## Step 3: Format

Run `ruff format` (and `ruff check --fix` if anything was changed).

## Step 4: Update Status

Most important! If `gre` exists (see the CLAUDE.local.md) make sure to update any nits (draft responses and/or auto_solve) that were associated with these fixes.