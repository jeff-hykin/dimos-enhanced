---
name: rrd-toolkit
description: >
  This skill should be used when the user asks to "inspect rrd", "query rerun recording",
  "look at the .rrd file", "what entities are in this recording", "what was the robot doing
  at time X", "point cloud size over time", "when was entity X near point Y", "resample
  odom at 10hz", or any other question about a Rerun .rrd recording file.
allowed-tools: [Bash, Read]
version: 0.1.0
---

# RRD Toolkit

A set of CLI tools for querying Rerun `.rrd` recording files. All tools emit JSON to stdout.

## Location

All tools are in `${CLAUDE_PLUGIN_ROOT}/scripts/`. Invoke as:

```
${CLAUDE_PLUGIN_ROOT}/scripts/rrd-entities file.rrd
```

Or (easier) add the scripts dir to PATH for the session:

```sh
export PATH="${CLAUDE_PLUGIN_ROOT}/scripts:$PATH"
rrd-entities file.rrd
```

## Prerequisites

The tools need a Python with `rerun-sdk[datafusion]` installed. They auto-detect one in
`~/repos/dimos*/.venv` and `~/repos/dimensional-applications/.venv`. Override with
`RRD_PYTHON=/path/to/python`.

## Tools

### Discovery / schema
| Tool | Purpose |
|---|---|
| `rrd-entities <file>` | List entity paths with row counts, archetypes, time ranges |
| `rrd-schema <file>` | Component schema grouped by archetype |
| `rrd-info <file>` | Recording metadata (store ID, SDK, time range, file size) |
| `rrd-timelines <file>` | List timelines with range and tick counts |
| `rrd-tf <file>` | Transform frame hierarchy |
| `rrd-warnings <file>` | Contents of `/__warnings` TextLog |

### Time / rate
| Tool | Purpose |
|---|---|
| `rrd-rate <file> [--entity PATH]` | Publishing rate (Hz), gap stats, duration |
| `rrd-gaps <file> --entity PATH [--threshold S]` | Gaps larger than threshold |
| `rrd-sample <file> --entity PATH --hz N [--values]` | Resample at fixed rate (nearest-neighbor) |

### Slicing
| Tool | Purpose |
|---|---|
| `rrd-head <file> --entity PATH [-n N \| --seconds S]` | First rows |
| `rrd-tail <file> --entity PATH [-n N \| --seconds S]` | Last rows |
| `rrd-slice <file> --entity PATH --start T --end T [--relative]` | Time range |
| `rrd-at <file> --entity PATH (--time T \| --ref OTHER --ref-event first\|last) [-n N]` | Nearest rows to a time |

### Value-level
| Tool | Purpose |
|---|---|
| `rrd-component <file> --entity PATH --component COMP [--start T --end T]` | Raw component values |
| `rrd-summary <file> --entity PATH --component COMP` | Per-row size/min/max/mean over time |
| `rrd-histogram <file> --entity PATH --component COMP --field (size\|x\|y\|z\|norm)` | Distribution |

### Relational / spatial (power tools)
| Tool | Purpose |
|---|---|
| `rrd-when <file> --entity PATH --component COMP --predicate EXPR` | Timestamps where predicate holds |
| `rrd-correlate <file> --entity-a A --entity-b B --when-a EXPR [--component-a/-b C]` | For each matching row of A, closest row of B |
| `rrd-near-point <file> --entity PATH --component COMP --point X,Y,Z --radius R` | Timestamps where position is within radius |

### Passthroughs
| Tool | Purpose |
|---|---|
| `rrd-print <file>` | Wraps `rerun rrd print` |
| `rrd-verify <file>` | Wraps `rerun rrd verify` |
| `rrd-stats <file>` | Wraps `rerun rrd stats` |

## Predicate syntax (for `rrd-when` and `rrd-correlate --when-a`)

The predicate runs once per row with the current component value bound. Available identifiers:

- `value` — the component value (e.g. `[x, y, z]` for `Transform3D:translation`, or list of vec3s for `Points3D:positions`)
- `size` — number of elements (number of points in a point cloud; `1` for a single vector)
- `x`, `y`, `z`, `w` — components of a single vector (if applicable)
- `translation`, `position`, `point` — aliases for `value`
- `shape` — numpy shape tuple

Functions: `norm`, `abs`, `min`, `max`, `len`, `sum`. Operators: `+ - * / < <= > >= == != and or not in`.

Examples:
- `'size > 10000'` — point cloud with > 10k points
- `'norm(value - [0,2,6]) < 1.0'` — position within 1m of (0,2,6)
- `'z < 0.5'` — height below 0.5m (single vector component)
- `'x > 0 and y > 0'` — in positive quadrant

Arbitrary Python is **not** allowed — parsed by whitelisted AST nodes only.

## Agent hints

- When the user says **"the robot"**, they typically mean `/world/odom` or `/world/corrected_odometry` or a similarly-named entity. Start by running `rrd-entities` and look for an odom-like entity.
- Entity paths in DimOS recordings are usually rooted at `/world/` (e.g. `/world/lidar`, `/world/color_image`, `/world/odom`, `/world/tf/<frame>`).
- "The point cloud" → `/world/lidar`. "The terrain/costmap" → `/world/global_costmap` or `/world/global_map`. "The camera" → `/world/color_image`.
- Always start with `rrd-entities` when you don't know the file's contents — it shows all entities with row counts and time ranges.
- Use `rrd-rate` early to spot rate anomalies or dropouts.
- For value queries, prefer `rrd-summary` over `rrd-component` when you just need sizes/stats — `rrd-component` can return huge point cloud arrays.
- To answer "how big was X when Y happened?": use `rrd-correlate` with `--when-a` on Y's condition and `--component-b` for X's component.

## Common recipes

**"How big was the point cloud when odom was near (0,2,6)?"**
```sh
rrd-correlate file.rrd \
    --entity-a /world/corrected_odometry --component-a Transform3D:translation \
    --when-a 'norm(value - [0,2,6]) < 1.0' \
    --entity-b /world/lidar --component-b Points3D:positions
```

**"Is lidar publishing at the expected rate?"**
```sh
rrd-rate file.rrd --entity /world/lidar
rrd-gaps file.rrd --entity /world/lidar --threshold 0.2
```

**"Resample odom at 10Hz"**
```sh
rrd-sample file.rrd --entity /world/corrected_odometry --hz 10 --values
```

**"What was the robot doing when the camera stopped?"**
```sh
rrd-at file.rrd --entity /world/corrected_odometry --ref /world/color_image --ref-event last -n 3
```
