---
globs: ["**/test_*.py", "**/tests/**", "**/conftest.py"]
---

# Testing Rules

## Running Tests

- Use `uv run pytest` for fast tests (excludes `slow`, `tool`, `mujoco` markers)
- Use `./bin/pytest-slow` for full CI tests (includes slow, excludes tool and mujoco)
- Single file: `uv run pytest path/to/test_file.py -v`
- Run `ruff check --fix && ruff format` after any Python changes

## Fixtures

- Check `conftest.py` files at all levels before creating new fixtures — reuse existing ones
- Import fixtures from shared conftest files rather than duplicating setup logic
- De-duplicate fixtures aggressively: if two tests need similar setup, extract a shared fixture
- Parametrize fixtures instead of creating near-identical variants

## Conventions

- Prefix manual test scripts with `demo_` to exclude from pytest collection
- Tests that need hardware or external services use the `tool` marker
- Tests that take >10s use the `slow` marker
- MuJoCo simulation tests use the `mujoco` marker

## CI Validation

- `bin/ci-fast`: quick checks + test suite
- `bin/ci-check`: linting and type checks only
- `bin/pr-check`: full PR validation (uv sync, pre-commit, mypy 3.10+3.12, pytest)
