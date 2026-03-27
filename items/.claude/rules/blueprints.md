---
globs: ["**/blueprints/**/*.py", "**/blueprints.py", "**/all_blueprints.py"]
---

# Blueprint Rules

- `autoconnect(*blueprints)` merges multiple blueprints, deduplicating modules (last wins)
- Blueprints are immutable — every config method (`.global_config()`, `.transports()`, `.remappings()`) returns a new Blueprint
- `dimos/robot/all_blueprints.py` is auto-generated. **DO NOT EDIT MANUALLY.** Regenerate with: `pytest dimos/robot/test_all_blueprints_generation.py`
- Top-level variable name becomes CLI name: `my_robot_basic` → `my-robot-basic`
- Expose blueprint as a module-level variable for `dimos run` to discover it
- Use both `McpServer.blueprint()` and `McpClient.blueprint()` when adding MCP to a blueprint
