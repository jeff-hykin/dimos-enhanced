---
globs: ["**/skill*.py", "**/annotation.py", "**/agents/**/*.py"]
---

# Skill & Agent Rules

## @skill Decorator

- `@skill` implies `@rpc` AND exposes the method to the LLM as a tool. **Do not stack both `@rpc` and `@skill`.**
- Docstring is **mandatory** — `ValueError` at startup if missing
- Type-annotate every parameter — missing annotation means no `"type"` in schema
- Return `str` — `None` return tells the agent "It has started. You will be updated later."
- Supported param types: `str`, `int`, `float`, `bool`, `list[str]`, `list[float]`. Avoid complex nested types.

## Spec Pattern (cross-module RPC)

- Declare a `Spec` Protocol for typed, build-time-checked cross-module references
- Annotate as `_navigator: NavigatorSpec` — injected by blueprint at build time
- If multiple modules match, use `.remappings()` to resolve
- **Legacy**: `rpc_calls: list[str]` + `get_rpc_calls()` still works but failures are silent. Don't use in new code.

## System Prompts

- Go2 default: `dimos/agents/system_prompt.py`
- G1 humanoid: `dimos/robot/unitree/g1/system_prompt.py`
- Always pass the robot-specific prompt: `McpClient.blueprint(system_prompt=G1_SYSTEM_PROMPT)`
