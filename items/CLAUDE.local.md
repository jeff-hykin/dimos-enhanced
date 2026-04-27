# DimOS Project Context

- make sure to use the `.venv` with uv whenever doing python stuff
- don't add verbose/noisey comments everywhere
- don't use short var names like `mod`, use a name like `module` instead
- every subscription needs an unsub handler `self.nav_cmd_vel.subscribe`
- in tests don't use stuff like `with patch.object(MovementManager, "__init__", lambda self: None):` because paul called it a "a very bad Claude pattern."
- if an import can be at the top it almost always should be


## What is DimOS

The agentic operating system for generalist robotics. `Modules` communicate via typed streams over LCM, ROS2, DDS, or other transports. `Blueprints` compose modules into runnable robot stacks. `Skills` give agents the ability to execute physical on-hardware functions like `grab()`, `follow_object()`, or `jump()`.

## Core Abstractions

- **Module** — A unit of computation with typed input/output streams, RPCs, and skills. **Modules are singletons** — each module class is instantiated exactly once per blueprint, and modules are only started once (no restart). This means a module instance can never race with another instance of itself, and you don't need to guard against duplicate startup or re-initialization.
- **Blueprint** — An immutable, composable description of which modules to run and how to wire them
- **Stream** — Typed pub/sub channels (`In[T]` / `Out[T]`) connecting modules
- **Transport** — The wire protocol for streams (LCM multicast by default)
- **Spec** — Protocol interfaces that let modules reference each other by capability, not class

## Key Files

| File | Purpose |
|------|---------|
| `dimos/core/module.py` | `ModuleBase` and `Module` base classes |
| `dimos/core/coordination/blueprints.py` | `Blueprint`, `_BlueprintAtom`, `autoconnect()` |
| `dimos/core/coordination/module_coordinator.py` | `ModuleCoordinator` — orchestrates deploy + lifecycle |
| `dimos/core/coordination/python_worker.py` | `PythonWorker`, `Actor` proxy (forkserver + pipe IPC) |
| `dimos/core/coordination/worker_manager_python.py` | `WorkerManagerPython` — manages worker pool |
| `dimos/core/coordination/worker_manager_docker.py` | `WorkerManagerDocker` — docker-based deployment |
| `dimos/core/stream.py` | `In[T]`, `Out[T]`, `Transport[T]` |
| `dimos/core/transport.py` | All transport implementations (LCM, SHM, ROS, DDS, Jpeg variants) |
| `dimos/core/rpc_client.py` | `RPCClient`, `ModuleProxy` — RPC wrappers over Actor |
| `dimos/core/global_config.py` | `GlobalConfig` (env vars, CLI flags, .env) |
| `dimos/agents/annotation.py` | `@skill` decorator |
| `dimos/spec/utils.py` | Spec protocol utilities |
| `dimos/robot/all_blueprints.py` | Auto-generated registry (DO NOT EDIT MANUALLY) |

Note: `dimos/core/blueprints.py` is a backwards-compat shim that re-exports from `dimos/core/coordination/blueprints.py`.

## Blueprint Build Timeline

When `ModuleCoordinator.build(blueprint)` is called, the sequence is:

1. **Configuration (HOST)** — Apply global_config_overrides then CLI overrides
2. **Validation (HOST)** — Run configurators, check requirements, verify no stream name conflicts
3. **Start Worker Pool (HOST)** — Spawn N forkserver worker subprocesses (via `PythonWorker`)
4. **Deploy Modules (HOST → WORKER/DOCKER)** — Instantiate each module in a worker or container via `deploy_parallel()`
5. **Connect Streams (HOST → WORKER via RPC)** — Match `(name, type)` pairs, assign transports
6. **Connect Module References (HOST → WORKER via RPC)** — Resolve Spec-based references
7. **Build All Modules (HOST → WORKER via RPC)** — Call `module.build()` on each in parallel (for heavy one-time work like docker builds, LFS downloads; 24h timeout)
8. **Start All Modules (HOST → WORKER via RPC)** — Call `module.start()` on each in parallel
9. **Log Blueprint Graph** — Render module graph to Rerun if RerunBridgeModule is active
10. **Return** — Caller uses `coordinator.loop()` to block or `coordinator.stop()` to tear down

Note: There is also `coordinator.load_blueprint()` for hot-loading additional blueprints into an already-running coordinator.

## CLI Quick Reference

```bash
dimos run <blueprint> [--daemon] [--disable MODULE]  # Start a blueprint
dimos status                        # Show running instance
dimos stop [--force]                # Graceful stop (or force kill)
dimos restart [--force]             # Restart with same arguments
dimos list                          # List all blueprints (excludes demo- prefixed)
dimos log [-f] [-n N] [--all] [--json] [--run ID]  # View logs
dimos show-config                   # Show current GlobalConfig values
dimos agent-send "<text>"           # Send text to running agent
dimos mcp list-tools                # List MCP skills
dimos mcp call <tool> [--arg K=V]   # Call an MCP tool
dimos mcp status                    # MCP server status
dimos mcp modules                   # List deployed modules and skills
dimos topic echo <topic> [type]     # Listen to a pub/sub topic
dimos topic send <topic> <expr>     # Publish to a pub/sub topic
dimos lcmspy                        # LCM message monitor
dimos agentspy                      # Agent monitor
dimos humancli                      # Interactive agent CLI
dimos top                           # Live resource monitor TUI
dimos rerun-bridge                  # Launch Rerun visualization bridge
```

Log files: `~/.local/state/dimos/logs/<run-id>/main.jsonl`

## Demo Preferences

- Demos should basically always use `autoconnect` for composing blueprints
- Prefer doing things inline/simple if they are not a part of the feature being demonstrated
- Don't over-abstract demo code — clarity and readability matter more than DRY in demos
- If it's not the thing you're showing off, keep it as minimal as possible

## Transports

- **LCMTransport**: Default for types with `lcm_encode`. Multicast UDP.
- **pLCMTransport**: Pickled LCM — auto-selected for types without `lcm_encode`.
- **SHMTransport/pSHMTransport**: Shared memory — use for images and point clouds.
- **JpegLcmTransport**: JPEG-compressed images over LCM.
- **JpegShmTransport**: JPEG-compressed images over shared memory.
- **ROSTransport**: ROS topic bridge.
- **DDSTransport**: DDS pub/sub — install with `uv sync --extra dds`.

## The `.ignore.enhance` Overlay System

This repo uses a **separate git repo** nested at `.ignore.enhance/` (remote: `jeff-hykin/dimos-enhanced`) to manage personal tooling, Claude config, and helper scripts without polluting the main dimos git history. Files in `.ignore.enhance/items/` are symlinked into the parent repo, and the symlinks are excluded from the main repo via `.git/info/exclude` (not `.gitignore`, so they're invisible to other contributors).

### `epull` and `epush`

These are shell commands (in `~/Commands/`) that sync the enhance overlay:

- **`epull`** — Walks up from `$PWD` to find `.ignore.enhance/`, runs `git pull` on it, then re-symlinks everything from `items/` into the parent repo and updates `.git/info/exclude`. Run this after cloning a dimos repo or when someone else pushed changes to `dimos-enhanced`.
- **`epush`** — Walks up from `$PWD` to find `.ignore.enhance/`, runs `git add -A && git commit -m "sync" && git pull --rebase && git push` on the enhance repo. Run this after editing any file inside `.ignore.enhance/items/` (including this file).

**Typical workflow:**
```bash
# After editing CLAUDE.local.md, bin scripts, or .claude/ rules:
epush          # commits + pushes the enhance repo

# On a different machine or after someone else pushed:
epull          # pulls latest + re-symlinks everything
```

### Adding Hidden `bin/` Commands

To add a new script that appears in the repo's `bin/` directory without being tracked by the main repo's git:

1. Create the script in `.ignore.enhance/items/bin/your_script`
2. Make it executable: `chmod +x .ignore.enhance/items/bin/your_script`
3. Run `epull` — this symlinks it into `bin/your_script` and adds `bin/your_script` to `.git/info/exclude`
4. Run `epush` — this commits the new script to the enhance repo

The symlink chain: `bin/your_script → .ignore.enhance/items/bin/your_script`

Existing enhance-managed bin scripts include: `ci-check`, `ci-fast`, `ci-slow`, `cld`, `cldr`, `gen-blue`, `get_pos`, `pr-check`, `pr-diff`, `pr-name-check`, `send_clicked_point`, `send_cmd_vel`, `smart-nav-clean`, `smart-nav-status`.

### Other Enhance-Managed Paths

- **`CLAUDE.local.md`** (this file) — symlinked from repo root
- **`.claude/`** — entire directory symlinked (commands, rules, skills)
- **`_help/`** — helper data files (DAGs, caches, flake configs)

# gre start

`gre` (GitHub Review Explorer) is the central place in this repo for tracking PR review feedback — comments, CI failures, and merge conflicts. **If you make a change that addresses a review item, update gre so the user's TUI reflects reality.** Stale state is worse than no state. If a single change covers multiple items, mark each one.

You're collaborating with the user — keep the state up to date without clobbering choices the user already made. Strict rules below.

## Finding items

The state YAML lives at the path printed by `gre info`. Most relevant commands:
- `gre list` — list unresolved items
- `gre list --type <comment|ci_failure|merge_conflict>`, `--category <…>`, `--status <…>` — filters
- `gre show <id>` — full details for one item; **read this before updating** so you know what's already there
- `gre info` — print the state YAML path

Item ids: `c0`, `c1`, …, `ci0`, …, `mc0`, …

## Updating: narrow rules

### Status — only set `auto_solved`
Once you've made the code change, run `gre set <id> status auto_solved`. The status badge flips to orange ◎ in the TUI. **Do NOT set any other status** — `unseen`, `unaddressed`, `asked_claude`, and `solved` are all user-managed.

### Category — only promote from `unknown`
First run `gre show <id>` and look at the `category` field.
- If it's `unknown`: pick one of `fix | discussion | wontfix | large_change` and set it (`gre set <id> category <…>`).
- If it's anything else: **leave it alone.** The user already categorized it.

### Notes — don't clobber
`gre note <id> "<text>"` overwrites whatever was there. Always read first:
1. `gre note <id>` (no args) prints the current note.
2. If empty: `gre note <id> "<your note>"`.
3. If non-empty: combine the existing note with your addition (preserve the user's content verbatim) and write the combined value. Easiest pattern via stdin:
   `{ gre note <id>; printf '\n\n<your addition>'; } | gre note <id> --stdin`

### Draft response — don't clobber
`gre draft <id>` works the same way. **Critical:** if a draft is non-empty, the user is mid-typing it. Do NOT overwrite their draft. Either:
- Skip the draft and put your suggested wording in `gre note <id>` instead (the user can copy it over manually), OR
- If you genuinely need to extend it, read first and write the combined version (same stdin pattern as notes).

### Summary — fill if empty, otherwise leave it
The summary is a one-liner shown in the TUI list view. If empty, set one. If already set, don't touch it.

## When you fix something

If a fix is a single focused change, make it as one commit. After committing:
1. `gre set <id> status auto_solved`
2. If category was `unknown`, set it (probably `fix`).
3. If summary was empty, set a one-liner.
4. Optionally add a `gre note` recording what changed and why (using the don't-clobber pattern).
5. **Update every related item.** If your single commit addresses multiple review items, mark each of them auto_solved.

If it's `wontfix` or needs discussion, capture your reasoning in notes/draft per the rules above and set category if it's still `unknown` — don't commit code.

## Do NOT call

- `gre send` — posts the draft to GitHub. User-only.
- `gre resolve` — resolves the thread on GitHub. User-only.

## Special case: reached via `cbg ask` from the gre TUI

If you arrived through a `cbg ask` (the user pressed `c` in their gre TUI on a specific item), the question payload wraps that item's full context in `<review-item>` XML. **Reply via `tell_session`** to the inbox in the cbg hint at the top — the first line of your reply becomes the toast the user sees. Posting only in channel chat will park the user's gre process indefinitely. Apply the rules above to update state alongside the reply.

# gre end
