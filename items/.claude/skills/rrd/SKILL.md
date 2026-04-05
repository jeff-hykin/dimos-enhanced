# Rerun .rrd File Inspector

Use this guide when the user asks you to inspect, query, or debug Rerun recording files (.rrd).

## What is .rrd?

`.rrd` (Rerun Data) is a binary recording format from [rerun.io](https://rerun.io). It stores:
- **Entities**: named paths like `/world/lidar`, `/world/tf/base_link`
- **Components**: typed data columns like `Points3D:positions`, `Transform3D:quaternion`, `Image:buffer`
- **Timelines**: index columns (frame number, timestamp, etc.)

Data is stored as Apache Arrow record batches in streaming chunks.

## Available Tools

### 1. Python helper: `.claude/tools/rrd_inspect.py`

**Basic inspection:**
```bash
# List all entity paths with row counts and component types
python .claude/tools/rrd_inspect.py entities <file.rrd>

# Show recording metadata (store ID, SDK version, total stats)
python .claude/tools/rrd_inspect.py info <file.rrd>

# Show full schema organized by archetype
python .claude/tools/rrd_inspect.py schema <file.rrd>

# Show transform frame hierarchy
python .claude/tools/rrd_inspect.py tf <file.rrd>

# Show logged warnings/errors
python .claude/tools/rrd_inspect.py warnings <file.rrd>
```

**Data inspection (YAML output):**
```bash
# Show first/last N rows of an entity
python .claude/tools/rrd_inspect.py head <file.rrd> -e /world/lidar -n 5
python .claude/tools/rrd_inspect.py tail <file.rrd> -e /world/odom -n 10
```

**Temporal analysis:**
```bash
# Show publishing rate (Hz) and time range for all entities
python .claude/tools/rrd_inspect.py rate <file.rrd>

# Detect gaps in publishing (default threshold: 1s)
python .claude/tools/rrd_inspect.py gaps <file.rrd> -e /world/color_image -t 2.0
```

**Cross-entity temporal queries:**
```bash
# Get lidar data at the moment camera last published
python .claude/tools/rrd_inspect.py at <file.rrd> -e /world/lidar --ref /world/color_image --ref-event last

# Get lidar data at the moment camera FIRST published
python .claude/tools/rrd_inspect.py at <file.rrd> -e /world/lidar --ref /world/color_image --ref-event first

# Get odom data at a specific timestamp
python .claude/tools/rrd_inspect.py at <file.rrd> -e /world/odom --time 2026-03-28T00:01:00

# Get 3 nearest lidar readings to when camera stopped
python .claude/tools/rrd_inspect.py at <file.rrd> -e /world/lidar --ref /world/color_image --ref-event last -n 3
```

### 2. Rerun CLI (more detailed but verbose)

```bash
# Print all chunks summary
rerun rrd print <file.rrd>

# Print specific entity with full data (-vvv = max verbosity)
rerun rrd print -vvv --entity /world/lidar <file.rrd>

# Transposed view (easier to read for wide tables)
rerun rrd print -vvv --transposed --entity /world/odom <file.rrd>

# Stats
rerun rrd stats <file.rrd>

# Verify integrity
rerun rrd verify <file.rrd>
```

### 3. Open in Viewer

```bash
rerun <file.rrd>
```

## Common Query Patterns

### "When the camera stopped sending data, how big was the lidar point cloud?"

```bash
# Step 1: Find when camera stopped
python .claude/tools/rrd_inspect.py tail <file.rrd> -e /world/color_image -n 1

# Step 2: Get the lidar data at that moment
python .claude/tools/rrd_inspect.py at <file.rrd> -e /world/lidar --ref /world/color_image --ref-event last

# Or combined: the `at` command does the timestamp lookup for you
```

### "Is the camera publishing at the expected rate?"

```bash
# Check rates for all entities
python .claude/tools/rrd_inspect.py rate <file.rrd>

# Look for gaps specifically in camera data (flag anything > 2s)
python .claude/tools/rrd_inspect.py gaps <file.rrd> -e /world/color_image -t 2.0
```

### "What was the robot doing when sensor X dropped out?"

```bash
# Find the last message from the dropped sensor
python .claude/tools/rrd_inspect.py tail <file.rrd> -e /world/<sensor> -n 1

# Query odom at that moment
python .claude/tools/rrd_inspect.py at <file.rrd> -e /world/odom --ref /world/<sensor> --ref-event last

# Query all TF frames at that moment
python .claude/tools/rrd_inspect.py at <file.rrd> -e /world/tf/base_link --ref /world/<sensor> --ref-event last
```

### "Are camera and lidar timestamps aligned?"

```bash
# Compare rates and time ranges
python .claude/tools/rrd_inspect.py rate <file.rrd>

# Check the first messages from each
python .claude/tools/rrd_inspect.py head <file.rrd> -e /world/color_image -n 1
python .claude/tools/rrd_inspect.py head <file.rrd> -e /world/lidar -n 1
```

### "Does the recording have actual image data or just camera parameters?"

```bash
# Check what components exist on the camera entity
python .claude/tools/rrd_inspect.py entities <file.rrd>
# Look for Image:buffer or EncodedImage:blob — if only Pinhole components, pixels are missing
```

## Common DimOS Entity Paths

| Path Pattern | Archetype | Description |
|---|---|---|
| `/world/color_image` | `Pinhole` + `Image`/`EncodedImage` | Camera feed (intrinsics + pixels) |
| `/world/depth_image` | `DepthImage` | Depth camera |
| `/world/lidar` | `Points3D` | Lidar point cloud |
| `/world/odom` | `Transform3D` | Robot odometry pose |
| `/world/tf/<frame>` | `Transform3D` | TF tree frames (base_link, camera_link, etc.) |
| `/world/global_map` | `Boxes3D` | Voxel map |
| `/world/global_costmap` | `Mesh3D` | Navigation costmap mesh |
| `/world/path` | `LineStrips3D` | Planned navigation path |
| `/__warnings` | `TextLog` | Runtime warnings |
| `/__properties` | `RecordingInfo` | Recording metadata |

## Common Component Types

**Transforms:**
- `Transform3D:quaternion` — rotation as [x, y, z, w]
- `Transform3D:translation` — position as [x, y, z]
- `Transform3D:parent_frame` — parent frame name (string)
- `Transform3D:child_frame` — child frame name (string)

**Camera:**
- `Pinhole:image_from_camera` — 3x3 intrinsics matrix
- `Pinhole:resolution` — [width, height]
- `Image:buffer` / `EncodedImage:blob` — pixel data

**3D Data:**
- `Points3D:positions` — Nx3 float array
- `Points3D:colors` — Nx4 RGBA
- `Boxes3D:centers`, `Boxes3D:half_sizes` — axis-aligned boxes
- `Mesh3D:vertex_positions`, `Mesh3D:triangle_indices` — triangle mesh

## Debugging Workflow

When investigating a recording issue:

1. **Start with `entities`** to see what data exists
2. **Check `rate`** to see publishing frequencies and detect anomalies
3. **Check `tf`** to understand the frame hierarchy
4. **Use `head`/`tail`** to inspect actual values
5. **Use `gaps`** to find publishing dropouts
6. **Use `at --ref`** to correlate data across entities at specific moments
7. **Compare expected vs actual** — e.g., if `/world/color_image` has Pinhole but no Image components, image data isn't being logged
8. **Check `warnings`** for runtime errors
9. **Open in viewer** (`rerun <file.rrd>`) for visual inspection
