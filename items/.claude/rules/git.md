---
globs: ["**"]
alwaysApply: true
---

# Git Rules

- **Never use `--no-verify`** when committing. If pre-commit fails, fix the underlying issue.
- Branch prefixes: `feat/`, `fix/`, `refactor/`, `docs/`, `test/`, `chore/`, `perf/`
- PRs target `dev` — never push to `main` or `dev` directly
- Don't force-push unless after a rebase with conflicts
- Minimize pushes — every push triggers CI (~1 hour on self-hosted runners). Batch commits locally, push once.
- Always activate the venv before committing: `source .venv/bin/activate`
- Pre-commit must pass. Install with: `uv pip install pre-commit && pre-commit install`

## Merging with dev — conventions.md check

When merging `dev` into a feature branch (or rebasing onto dev), **always check for convention changes**:

1. Run `git diff dev...HEAD -- conventions.md` and `git diff HEAD...dev -- conventions.md` to see if `conventions.md` was added or changed on either side.
2. If dev has convention changes, read the full current `conventions.md` after merging. Conventions can be anything — naming patterns, architectural rules, import style, error handling approaches, API design patterns, documentation requirements, config formats, etc.
3. Get the list of all files changed on your branch: `git diff dev...HEAD --name-only`. Read through each one and check whether it follows every convention in the current `conventions.md`. Fix any violations.

This matters because convention changes on dev won't produce merge conflicts with new code on your branch — git merges them cleanly since they touch different files. But the branch code may silently violate the new conventions. For example: dev adds "all modules must implement `build()` as an `@rpc`" — your branch's new module won't conflict but will be wrong if it doesn't follow that pattern.
