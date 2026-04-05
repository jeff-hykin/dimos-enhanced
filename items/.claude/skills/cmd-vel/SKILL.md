---
name: cmd-vel
description: Send velocity commands, nav goals, and inspect pose/LCM topics on the running robot. Covers bin/send_cmd_vel, bin/send_clicked_point, bin/get_pos, bin/debug_nav.py, and dimos run/stop/status/log with DISPLAY caveats for running nav sims safely.
allowed-tools: Bash, Read, Grep, Glob
---

# Robot control & nav debugging

A running DimOS instance (real robot or sim) exposes LCM topics you can
publish to / subscribe from using the scripts in `bin/`. This skill
documents all of them plus the `dimos` CLI for running/stopping the stack.

Always activate the venv first:

```
source .venv/bin/activate
```

## DISPLAY caveats — READ BEFORE RUNNING A SIM

On this machine `DISPLAY=:1` is the **user's actual desktop session**
(the only X socket in `/tmp/.X11-unix/` is `X1`). Starting
`unitree-g1-nav-sim` (Unity-backed) with
`DISPLAY=:1` pops simulator windows onto the real desktop. A heavy
sim has previously taken the whole session down (including VS Code).

Guidance:

- **Do not** run `DISPLAY=:1 dimos run unitree-g1-nav-sim --daemon`
  unless the user explicitly asks you to render to their desktop.
- Prefer: start the sim without setting DISPLAY at all, or with
  `DISPLAY=:0` (virtual/headless). The sim may still spawn GPU/GL
  processes — monitor with `dimos log -n 200` right after start.
- If the user wants visuals, suggest they start Xvfb or use the
  rerun viewer in a separate terminal rather than piping the sim
  into `:1`.

## `dimos` CLI

```
dimos run <blueprint> [--daemon]    # start a blueprint (e.g. unitree-g1-nav-sim)
dimos status                        # show the running instance (pid, run-id)
dimos stop [--force]                # stop gracefully, or --force kill
dimos list                          # list all discoverable blueprints
dimos log [-f] [-n N]               # tail logs (main.jsonl)
```

Logs live under `~/.local/state/dimos/logs/<run-id>/main.jsonl`.
Use `dimos log -n 500 | grep "\[local_planner\]"` to grep C++
stderr from a specific native module.

Always `dimos stop` when finished, and verify with `dimos status`
that no stale instance is left.

## `bin/send_cmd_vel` — direct velocity

```
source .venv/bin/activate && python bin/send_cmd_vel <linear_x> <linear_y> <angular_z> [duration]
```

Publishes `TwistDuration` on `/agent_cmd_vel`. Default duration is 1s.
The script sends a 5-message burst so the cmd-vel mux registers it.

Parse user intent:
- "forward" → +linear_x (default 0.5)
- "backward" → -linear_x
- "left" (strafe) → +linear_y
- "right" (strafe) → -linear_y
- "turn left" → +angular_z
- "turn right" → -angular_z
- "stop" → `0 0 0`
- bare "cmd-vel" with no args → send stop

## `bin/send_clicked_point` — nav goal

```
source .venv/bin/activate && python bin/send_clicked_point <x> <y> [z]
```

Publishes `PointStamped` on `/clicked_point`. Coordinates are meters in
the `map` frame. `z` defaults to 0. The running `ClickToGoal` module
picks this up and routes it to `FarPlanner` (or `TarePlanner`) which
in turn produces way_points for `LocalPlanner`.

## `bin/get_pos` — stream odometry

```
source .venv/bin/activate && bin/get_pos
```

Subscribes to `/odometry` and prints `pos=(x,y,z) vel=(vx,vy,vz)` at
5 Hz. Run in a separate terminal (or with `run_in_background`) while
sending goals to observe the robot's response.

## `bin/debug_nav.py` — general LCM topic introspection

Inspect its `--help` or source to see subscribable topics. Useful for
one-shot reads of `obstacle_cloud`, `path`, `goal_path`, `way_point`,
`terrain_map`, etc. to sanity-check what each module is publishing.

## Typical debug loop for nav issues

1. `source .venv/bin/activate && dimos run unitree-g1-nav-sim --daemon`
   (no DISPLAY — see caveats above).
2. Confirm with `dimos status`. Check first 200 log lines:
   `dimos log -n 200`.
3. In a separate bg process, tail module stderr of interest:
   `dimos log -f | grep "\[local_planner\]"`.
4. `bin/get_pos` in another bg process for pose/vel samples.
5. Send ONE goal with `bin/send_clicked_point <x> <y>`.
6. Observe: expected log cadence, pose progression, velocity sign
   stability. Sign flips during straight-line travel = stutter.
7. Form hypothesis, edit code, rebuild (native modules rebuild on
   `rebuild_on_change` file edits automatically next `dimos run`),
   re-test.
8. `dimos stop` when done.
