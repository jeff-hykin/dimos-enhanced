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
2. If dev introduced convention changes (e.g. renamed `global_config` → `global_conf`, changed import paths, renamed modules), those changes won't cause merge conflicts in new files your branch added — but those new files will silently use the old conventions and be broken.
3. After merging, read the current `conventions.md` and scan all files changed on your branch (`git diff dev...HEAD --name-only`) for violations of the updated conventions. Fix any that use the old names/patterns.

This is critical because convention renames (function names, module paths, config keys) in dev won't conflict with brand-new files on your branch — git sees them as unrelated changes — but the new files will reference symbols that no longer exist.
