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
