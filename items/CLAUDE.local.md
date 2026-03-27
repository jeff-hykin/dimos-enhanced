# DimOS Project Context

## What is DimOS

The agentic operating system for generalist robotics. `Modules` communicate via typed streams over LCM, ROS2, DDS, or other transports. `Blueprints` compose modules into runnable robot stacks. `Skills` give agents the ability to execute physical on-hardware functions like `grab()`, `follow_object()`, or `jump()`.

## Core Abstractions

- **Module** — A unit of computation with typed input/output streams, RPCs, and skills
- **Blueprint** — An immutable, composable description of which modules to run and how to wire them
- **Stream** — Typed pub/sub channels (`In[T]` / `Out[T]`) connecting modules
- **Transport** — The wire protocol for streams (LCM multicast by default)
- **Spec** — Protocol interfaces that let modules reference each other by capability, not class

## Key Files

| File | Purpose |
|------|---------|
| `dimos/core/module.py` | `ModuleBase` and `Module` base classes |
| `dimos/core/blueprints.py` | `Blueprint`, `_BlueprintAtom`, `autoconnect()` |
| `dimos/core/stream.py` | `In[T]`, `Out[T]`, `Transport[T]` |
| `dimos/core/transport.py` | `LCMTransport`, `pLCMTransport` |
| `dimos/core/module_coordinator.py` | Orchestrates deploy + lifecycle |
| `dimos/core/worker.py` | Worker subprocess management, `Actor` proxy |
| `dimos/core/global_config.py` | `GlobalConfig` (env vars, CLI flags, .env) |
| `dimos/agents/annotation.py` | `@skill` decorator |
| `dimos/spec/utils.py` | Spec protocol utilities |
| `dimos/robot/all_blueprints.py` | Auto-generated registry (DO NOT EDIT MANUALLY) |

## Blueprint Build Timeline

When `blueprint.build()` is called, the sequence is:

1. **Configuration (HOST)** — Apply global_config_overrides then CLI overrides
2. **Validation (HOST)** — Run configurators, check requirements, verify no stream name conflicts
3. **Start Worker Pool (HOST)** — Spawn N forkserver worker subprocesses
4. **Deploy Modules (HOST → WORKER/DOCKER)** — Instantiate each module in a worker or container, set up RPC
5. **Connect Streams (HOST → WORKER via RPC)** — Match `(name, type)` pairs, assign transports
6. **Connect RPCs (HOST → WORKER via RPC)** — Wire up cross-module RPC callables
7. **Connect Module References (HOST → WORKER via RPC)** — Resolve Spec-based references
8. **Start All Modules (HOST → WORKER via RPC)** — Call `module.start()` on each in parallel
9. **Return** — Caller uses `coordinator.loop()` to block or `coordinator.stop()` to tear down

## CLI Quick Reference

```bash
dimos run <blueprint> [--daemon]    # Start a blueprint
dimos status                        # Show running instance
dimos stop [--force]                # Graceful stop (or force kill)
dimos list                          # List all blueprints
dimos log [-f] [-n N]               # View logs
dimos mcp list-tools                # List MCP skills
dimos agent-send "<text>"           # Send text to running agent
```

Log files: `~/.local/state/dimos/logs/<run-id>/main.jsonl`

## Demo Preferences

- Demos should basically always use `autoconnect` for composing blueprints
- Prefer doing things inline/simple if they are not a part of the feature being demonstrated
- Don't over-abstract demo code — clarity and readability matter more than DRY in demos
- If it's not the thing you're showing off, keep it as minimal as possible

## Transports

- **LCMTransport**: Default. Multicast UDP.
- **SHMTransport/pSHMTransport**: Shared memory — use for images and point clouds.
- **pLCMTransport**: Pickled LCM — use for complex Python objects.
- **ROSTransport**: ROS topic bridge.
- **DDSTransport**: DDS pub/sub — install with `uv sync --extra dds`.
