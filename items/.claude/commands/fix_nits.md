# Fix Nits

Fix common style/correctness nits across the files that would be part of a PR review.

## Step 1: Get the files in scope

Get all the files that would be part of a PR review:

```bash
git fetch origin dev --quiet
git diff $(git merge-base origin/dev HEAD)..HEAD
```

## Step 2: Within those files, check the following

- grep for `self.<word>._transport`, we should basically never use `_transport`, that usually indicates that a start method forgot to have a `@rpc` decorator. **Same applies in tests** — use `port.publish(...)` / `port.subscribe(...)`, never `port._transport.publish(...)` / `port._transport.subscribe(...)`.
- Use grep to find every `def start` and check all subscribe calls within the body. Every `start` should:
    - have an `@rpc` decorator
    - begin with `super().start()`
    - wrap every `subscribe` with `register_disposable`, e.g.
      `self.register_disposable(Disposable(self.agent.subscribe(self._on_agent_message)))`
- In tests, every bare subscribe — including raw LCM (`lc.subscribe(...)`) and port subscribes — must be paired with cleanup. Either wrap with `register_disposable` (when a coordinator is in scope) or explicitly unsubscribe in a `finally` / fixture teardown. Leaked subscriptions corrupt later tests.
- In tests, every `threading.Thread(...)` must be assigned to a variable so it can be `join()`-ed during teardown. Fire-and-forget `threading.Thread(target=...).start()` outlives the test.
- In tests, no `print()` calls. Use `logging` if diagnostics are genuinely needed; otherwise rely on assertion messages and pytest output.
- In tests, prefer `assert x == pytest.approx(y)` over `math.isclose(x, y)` — `pytest.approx` produces a useful failure message, `math.isclose` just prints `False`.
- Use grep to find any indented (non-top-level) import statements. If they can be moved to the top of the file without a performance penalty (e.g. `from typing import Any`), move them. **In test files this is strict** — never put imports inside test functions, methods, or fixtures.
- Use grep to find every `# type: ignore` (and similar typing-ignore comments). Confirm each one is still actually needed; remove the ones that aren't. **In test files**, also remove plain parameter annotations that exist only to silence the type checker — tests don't need typechecking, and `# type: ignore[no-untyped-def]` on test helpers should be deleted along with the annotation.
- For functions that legitimately take `**kwargs`, the annotation should be `**kwargs: Any` (from `typing`), never `**kwargs: object`.
- `__init__` must stay declarative: assign fields, call `super().__init__()`, and stop. Move validation, network probes, file existence checks, and any I/O to `build()` or `start()`. If you find `self._validate_*()`, network calls, or file checks in a constructor, relocate them. This is also the reason tests resort to monkey-patching `__init__` / `__new__` — Paul's "very bad Claude pattern" comes from this.
- Use LSP tools to check for any dead code in those changes
- if there are magic numbers like `70` or `2.5` or `30` make sure they are in a describptive variable
- Run `tree` on the `docs/` dir and see if there are any docs that need updating based on changes made to the code.
- Read all the docstrings and comments in the changed files. Remove any that are junk/noise. Example of noise to delete:
  ```python
  # create nav stack
  n = create_nav_stack()
  ```
  Also delete decorative section headers like `# Test`, ASCII docstring banners, and per-attribute "this is the X for Y" comments when the surrounding code already conveys it. **An empty `\`\`\`suggestion\`\`\`** block from a reviewer means *delete the lines it covers*.
- Grep for all module definitions and make sure there are no `__setstate__` or `__getstate__` methods on modules — they have no purpose and should be removed. If they were added to "fix" a pickling error on a `threading.Lock` or similar field, lazy-init that field in `start()` instead.
- While doing the above, if any variable names are shortened (e.g. `mod` instead of `module`, `lc` instead of `lcm`), expand them to the full word.

## Step 3: Format

Run `ruff format` (and `ruff check --fix` if anything was changed).

## Step 4: Update Status

Most important! If `gre` exists (see the CLAUDE.local.md) make sure to update any nits (draft responses and/or auto_solve) that were associated with these fixes.