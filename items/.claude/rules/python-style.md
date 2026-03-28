---
globs: ["**/*.py"]
---

# Python Style Rules

- Imports at top of file. No inline imports unless there is a circular dependency.
- Use `requests` for HTTP (not `urllib`). Use `Any` (not `object`) for JSON values.
- Type annotations required on all functions. Mypy strict mode.
- Don't hardcode ports or URLs — use `GlobalConfig` constants.
- Run `ruff check --fix && ruff format` after every Python change.
- Prefix manual test scripts with `demo_` to exclude from pytest collection.
- No magic numbers. If the reason for a numeric literal isn't immediately obvious, assign it to a named variable or constant. Numbers like `0`, `1`, `-1`, `2` (halving/doubling), `3.14159`, `100` (percent), `1000` (ms↔s) are usually fine inline. When in doubt, name it.
