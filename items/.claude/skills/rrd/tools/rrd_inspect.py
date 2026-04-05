# Copyright 2025-2026 Dimensional Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""CLI tool for inspecting Rerun .rrd recording files.

Usage::

    python -m dimos.utils.rrd_inspect <command> <file.rrd> [options]

Commands::

    entities    List all entity paths with their data types and row counts
    head        Show the first N rows of an entity
    tail        Show the last N rows of an entity
    schema      Show the full schema (timelines + component columns)
    tf          Show the transform frame hierarchy
    info        Show recording metadata
    warnings    Show any logged warnings/errors
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path


def _run_rrd_print(
    rrd_path: str,
    *,
    entity: str | None = None,
    verbose: int = 0,
) -> str:
    cmd = ["rerun", "rrd", "print"]
    if verbose > 0:
        cmd.append("-" + "v" * verbose)
    if entity:
        cmd.extend(["--entity", entity])
    cmd.append(rrd_path)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return result.stdout + result.stderr


def _parse_chunks(output: str) -> list[dict]:
    """Parse rerun rrd print output into structured chunk info."""
    chunks = []
    for line in output.splitlines():
        # Match: Chunk(...) with N rows (SIZE) - /entity/path - data columns: [...]
        m = re.match(
            r"Chunk\((\S+)\) with (\d+) rows \(([^)]+)\) - (/\S+) - data columns: \[([^\]]*)\]",
            line,
        )
        if m:
            chunk_id, rows, size, entity, columns = m.groups()
            chunks.append(
                {
                    "chunk_id": chunk_id,
                    "rows": int(rows),
                    "size": size.strip(),
                    "entity": entity,
                    "columns": [c.strip() for c in columns.split() if c.strip()],
                }
            )
    return chunks


def cmd_entities(rrd_path: str, **_kwargs: object) -> None:
    """List all entity paths with data types and row counts."""
    output = _run_rrd_print(rrd_path)
    chunks = _parse_chunks(output)

    entities: dict[str, dict] = {}
    for c in chunks:
        e = c["entity"]
        if e not in entities:
            entities[e] = {"rows": 0, "size_parts": [], "columns": set()}
        entities[e]["rows"] += c["rows"]
        entities[e]["size_parts"].append(c["size"])
        entities[e]["columns"].update(c["columns"])

    print(f"{'Entity':<40} {'Rows':>6}  Components")
    print("-" * 90)
    for entity in sorted(entities):
        info = entities[entity]
        cols = ", ".join(sorted(info["columns"]))
        print(f"{entity:<40} {info['rows']:>6}  {cols}")


def cmd_schema(rrd_path: str, **_kwargs: object) -> None:
    """Show full schema: timelines and component columns."""
    output = _run_rrd_print(rrd_path, verbose=1)
    chunks = _parse_chunks(output)

    all_columns: set[str] = set()
    for c in chunks:
        all_columns.update(c["columns"])

    # Extract archetype:component pairs
    archetypes: dict[str, set[str]] = defaultdict(set)
    for col in sorted(all_columns):
        if ":" in col:
            arch, comp = col.split(":", 1)
            archetypes[arch].add(comp)
        else:
            archetypes["(other)"].add(col)

    print("=== Component Columns by Archetype ===\n")
    for arch in sorted(archetypes):
        print(f"  {arch}:")
        for comp in sorted(archetypes[arch]):
            print(f"    - {comp}")
        print()


def _parse_table_rows(output: str) -> tuple[list[str], list[dict[str, str]]]:
    """Parse the verbose rerun table output into column names and row dicts.

    The rerun output uses box-drawing characters. Data rows look like:
    │ │ row_XXXXX  ┆ 12  ┆ 2026-...  ┆ [[0.1, 0.2]]  ┆ [[0.3, 0.4]] │ │
    """
    columns: list[str] = []
    rows: list[dict[str, str]] = []

    # Annotation keywords that appear in header rows, not data
    skip_prefixes = ("type:", "kind:", "---", "ARROW:", "index_name:", "is_sorted:", "archetype:", "component:", "component_type:")

    for line in output.splitlines():
        if "┆" not in line:
            continue
        # Strip outer box-drawing: remove leading/trailing │ and whitespace
        raw = line.replace("│", "").strip()
        cells = [c.strip() for c in raw.split("┆")]

        if not columns:
            # First row with ┆ is the header
            columns = cells
            continue

        if len(cells) != len(columns):
            continue

        # Skip annotation rows (type:, kind:, ---, ARROW:, etc.)
        if any(c.startswith(skip_prefixes) for c in cells if c):
            continue

        rows.append(dict(zip(columns, cells)))

    return columns, rows


def _rows_to_yaml(columns: list[str], rows: list[dict[str, str]], entity: str) -> str:
    """Convert parsed rows to a readable YAML-ish format."""
    # Skip RowId column for readability
    display_cols = [c for c in columns if c != "RowId"]
    lines = [f"entity: {entity}", f"total_rows: {len(rows)}", "rows:"]
    for i, row in enumerate(rows):
        lines.append(f"  - # row {i}")
        for col in display_cols:
            val = row.get(col, "")
            lines.append(f"    {col}: {val}")
    return "\n".join(lines)


def cmd_head(rrd_path: str, entity: str, n: int = 5, **_kwargs: object) -> None:
    """Show the first N rows of an entity in YAML format."""
    if not entity:
        print("Error: --entity is required for head command", file=sys.stderr)
        sys.exit(1)
    output = _run_rrd_print(rrd_path, entity=entity, verbose=3)
    columns, rows = _parse_table_rows(output)
    if not rows:
        print(f"No data rows found for {entity}")
        return
    selected = rows[:n]
    print(_rows_to_yaml(columns, selected, entity))
    if len(rows) > n:
        print(f"  # ... {len(rows) - n} more rows")


def cmd_tail(rrd_path: str, entity: str, n: int = 5, **_kwargs: object) -> None:
    """Show the last N rows of an entity in YAML format."""
    if not entity:
        print("Error: --entity is required for tail command", file=sys.stderr)
        sys.exit(1)
    output = _run_rrd_print(rrd_path, entity=entity, verbose=3)
    columns, rows = _parse_table_rows(output)
    if not rows:
        print(f"No data rows found for {entity}")
        return
    selected = rows[-n:]
    start_idx = max(0, len(rows) - n)
    if start_idx > 0:
        print(f"  # skipped first {start_idx} rows")
    print(_rows_to_yaml(columns, selected, entity))


def cmd_tf(rrd_path: str, **_kwargs: object) -> None:
    """Show the transform frame hierarchy."""
    output = _run_rrd_print(rrd_path, verbose=3)

    # Parse parent_frame relationships from Transform3D chunks
    frames: dict[str, str | None] = {}  # child -> parent
    for line in output.splitlines():
        # Look for parent_frame values in the data
        if "parent_frame" in line.lower() and "│" in line:
            continue  # skip header rows

    # Fallback: parse from chunk summary to build hierarchy from entity paths
    chunks = _parse_chunks(_run_rrd_print(rrd_path))
    tf_entities = sorted(set(c["entity"] for c in chunks if "/tf/" in c["entity"]))
    transform_entities = sorted(
        set(c["entity"] for c in chunks if any("Transform3D" in col for col in c["columns"]))
    )

    if tf_entities:
        print("=== Transform Frame Entities ===\n")
        # Build tree from paths
        for entity in tf_entities:
            parts = entity.split("/")
            depth = len(parts) - 1
            frame_name = parts[-1]
            # Check for parent_frame column
            has_parent = any(
                "parent_frame" in col
                for c in chunks
                if c["entity"] == entity
                for col in c["columns"]
            )
            info_parts = []
            matching = [c for c in chunks if c["entity"] == entity]
            for c in matching:
                cols = [col for col in c["columns"] if "Transform3D" in col]
                if cols:
                    info_parts.append(f"{c['rows']} rows, components: {', '.join(cols)}")
            info = "; ".join(info_parts) if info_parts else ""
            print(f"  {'  ' * (depth - 2)}{frame_name}  ({info})")

    if transform_entities:
        non_tf = [e for e in transform_entities if "/tf/" not in e]
        if non_tf:
            print("\n=== Other Entities with Transforms ===\n")
            for entity in non_tf:
                matching = [c for c in chunks if c["entity"] == entity]
                rows = sum(c["rows"] for c in matching)
                cols = set()
                for c in matching:
                    cols.update(col for col in c["columns"] if "Transform3D" in col)
                print(f"  {entity}  ({rows} rows, {', '.join(sorted(cols))})")


def cmd_info(rrd_path: str, **_kwargs: object) -> None:
    """Show recording metadata."""
    output = _run_rrd_print(rrd_path)
    # Print everything before first Chunk line
    for line in output.splitlines():
        if line.startswith("Chunk("):
            break
        # Skip warnings
        if line.startswith("[") and "WARN" in line:
            continue
        if line.strip():
            print(line)

    # Summary stats
    chunks = _parse_chunks(output)
    entities = set(c["entity"] for c in chunks)
    total_rows = sum(c["rows"] for c in chunks)
    print(f"\nTotal entities: {len(entities)}")
    print(f"Total chunks: {len(chunks)}")
    print(f"Total rows: {total_rows}")
    print(f"File size: {Path(rrd_path).stat().st_size / 1024 / 1024:.1f} MB")


def cmd_warnings(rrd_path: str, **_kwargs: object) -> None:
    """Show any logged warnings/errors from the recording."""
    output = _run_rrd_print(rrd_path, entity="/__warnings", verbose=3)
    columns, rows = _parse_table_rows(output)
    if not rows:
        print("No warnings found in recording.")
        return
    print(_rows_to_yaml(columns, rows, "/__warnings"))


def _get_timestamps(rrd_path: str, entity: str) -> list[str]:
    """Extract log_time values for an entity."""
    output = _run_rrd_print(rrd_path, entity=entity, verbose=3)
    _, rows = _parse_table_rows(output)
    return [r["log_time"] for r in rows if r.get("log_time")]


def _parse_timestamp(ts: str) -> float | None:
    """Parse a rerun timestamp string to epoch seconds."""
    from datetime import datetime, timezone

    ts = ts.strip()
    if not ts:
        return None
    try:
        # Format: 2026-03-28T00:00:44.575916
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except ValueError:
        return None


def _find_nearest_row(
    rows: list[dict[str, str]], target_ts: float
) -> dict[str, str] | None:
    """Find the row with log_time closest to target_ts."""
    best = None
    best_diff = float("inf")
    for row in rows:
        ts = _parse_timestamp(row.get("log_time", ""))
        if ts is None:
            continue
        diff = abs(ts - target_ts)
        if diff < best_diff:
            best_diff = diff
            best = row
    return best


def cmd_rate(rrd_path: str, **_kwargs: object) -> None:
    """Show publishing rate (Hz) and time range for each entity."""
    output = _run_rrd_print(rrd_path)
    chunks = _parse_chunks(output)
    entity_names = sorted(set(c["entity"] for c in chunks if not c["entity"].startswith("/__")))

    print(f"{'Entity':<40} {'Rows':>6}  {'Hz':>8}  {'Duration':>10}  Time Range")
    print("-" * 120)

    for entity_name in entity_names:
        timestamps = _get_timestamps(rrd_path, entity_name)
        parsed = [t for t in (_parse_timestamp(ts) for ts in timestamps) if t is not None]
        total_rows = len(parsed)

        if len(parsed) < 2:
            print(f"{entity_name:<40} {total_rows:>6}  {'N/A':>8}  {'N/A':>10}  {timestamps[0] if timestamps else 'N/A'}")
            continue

        duration = parsed[-1] - parsed[0]
        hz = (len(parsed) - 1) / duration if duration > 0 else 0
        print(
            f"{entity_name:<40} {total_rows:>6}  {hz:>7.1f}  {duration:>9.1f}s  "
            f"{timestamps[0]} → {timestamps[-1]}"
        )


def cmd_gaps(rrd_path: str, entity: str, threshold: float = 1.0, **_kwargs: object) -> None:
    """Detect gaps in publishing for an entity (default threshold: 1s)."""
    if not entity:
        print("Error: --entity is required for gaps command", file=sys.stderr)
        sys.exit(1)

    timestamps = _get_timestamps(rrd_path, entity)
    parsed = [(_parse_timestamp(ts), ts) for ts in timestamps]
    parsed = [(epoch, raw) for epoch, raw in parsed if epoch is not None]

    if len(parsed) < 2:
        print(f"Not enough data points for {entity} (need at least 2, got {len(parsed)})")
        return

    # Compute intervals
    intervals = []
    for i in range(1, len(parsed)):
        dt = parsed[i][0] - parsed[i - 1][0]
        intervals.append(dt)

    avg_interval = sum(intervals) / len(intervals)
    gaps_found = []
    for i, dt in enumerate(intervals):
        if dt >= threshold:
            gaps_found.append({
                "from": parsed[i][1],
                "to": parsed[i + 1][1],
                "gap_seconds": round(dt, 3),
                "row_index": i,
            })

    print(f"entity: {entity}")
    print(f"total_rows: {len(parsed)}")
    print(f"avg_interval: {avg_interval:.4f}s ({1/avg_interval:.1f} Hz)" if avg_interval > 0 else "avg_interval: N/A")
    print(f"threshold: {threshold}s")
    print(f"gaps_found: {len(gaps_found)}")

    if gaps_found:
        print("gaps:")
        for g in gaps_found:
            print(f"  - from: {g['from']}")
            print(f"    to: {g['to']}")
            print(f"    gap_seconds: {g['gap_seconds']}")
            print(f"    after_row: {g['row_index']}")
    else:
        print("  (no gaps above threshold)")


def cmd_at(
    rrd_path: str, entity: str, time: str | None = None, ref_entity: str | None = None,
    ref_event: str = "last", n: int = 1, **_kwargs: object,
) -> None:
    """Query entity data at a specific time or relative to another entity's event.

    Examples:
      at -e /world/lidar --time 2026-03-28T00:01:00
      at -e /world/lidar --ref /world/color_image --ref-event last
      at -e /world/lidar --ref /world/color_image --ref-event first
    """
    if not entity:
        print("Error: --entity is required", file=sys.stderr)
        sys.exit(1)

    # Determine target timestamp
    target_ts: float | None = None

    if time:
        target_ts = _parse_timestamp(time)
        if target_ts is None:
            print(f"Error: could not parse timestamp '{time}'", file=sys.stderr)
            sys.exit(1)
        source_desc = f"time={time}"
    elif ref_entity:
        ref_timestamps = _get_timestamps(rrd_path, ref_entity)
        ref_parsed = [(_parse_timestamp(ts), ts) for ts in ref_timestamps]
        ref_parsed = [(epoch, raw) for epoch, raw in ref_parsed if epoch is not None]
        if not ref_parsed:
            print(f"Error: no timestamps found for ref entity {ref_entity}", file=sys.stderr)
            sys.exit(1)
        if ref_event == "last":
            target_ts, raw_ts = ref_parsed[-1]
            source_desc = f"last message of {ref_entity} at {raw_ts}"
        elif ref_event == "first":
            target_ts, raw_ts = ref_parsed[0]
            source_desc = f"first message of {ref_entity} at {raw_ts}"
        else:
            print(f"Error: unknown ref-event '{ref_event}', use 'first' or 'last'", file=sys.stderr)
            sys.exit(1)
    else:
        print("Error: provide --time or --ref", file=sys.stderr)
        sys.exit(1)

    # Load target entity data
    output = _run_rrd_print(rrd_path, entity=entity, verbose=3)
    columns, rows = _parse_table_rows(output)
    if not rows:
        print(f"No data found for {entity}")
        return

    # Find nearest rows
    rows_with_ts = []
    for row in rows:
        ts = _parse_timestamp(row.get("log_time", ""))
        if ts is not None:
            rows_with_ts.append((ts, row))
    rows_with_ts.sort(key=lambda x: abs(x[0] - target_ts))

    selected = [row for _, row in rows_with_ts[:n]]

    print(f"query: {entity} at {source_desc}")
    if selected:
        nearest_ts = _parse_timestamp(selected[0].get("log_time", ""))
        if nearest_ts is not None:
            print(f"time_offset: {nearest_ts - target_ts:+.4f}s")
    print(_rows_to_yaml(columns, selected, entity))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inspect Rerun .rrd recording files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # entities
    p = sub.add_parser("entities", help="List all entity paths with data types")
    p.add_argument("rrd_path", help="Path to .rrd file")

    # schema
    p = sub.add_parser("schema", help="Show full schema")
    p.add_argument("rrd_path", help="Path to .rrd file")

    # head
    p = sub.add_parser("head", help="Show first N rows of an entity")
    p.add_argument("rrd_path", help="Path to .rrd file")
    p.add_argument("--entity", "-e", required=True, help="Entity path")
    p.add_argument("-n", type=int, default=5, help="Number of rows")

    # tail
    p = sub.add_parser("tail", help="Show last N rows of an entity")
    p.add_argument("rrd_path", help="Path to .rrd file")
    p.add_argument("--entity", "-e", required=True, help="Entity path")
    p.add_argument("-n", type=int, default=5, help="Number of rows")

    # tf
    p = sub.add_parser("tf", help="Show transform frame hierarchy")
    p.add_argument("rrd_path", help="Path to .rrd file")

    # info
    p = sub.add_parser("info", help="Show recording metadata")
    p.add_argument("rrd_path", help="Path to .rrd file")

    # warnings
    p = sub.add_parser("warnings", help="Show logged warnings/errors")
    p.add_argument("rrd_path", help="Path to .rrd file")

    # rate
    p = sub.add_parser("rate", help="Show publishing rate per entity")
    p.add_argument("rrd_path", help="Path to .rrd file")

    # gaps
    p = sub.add_parser("gaps", help="Detect gaps in publishing")
    p.add_argument("rrd_path", help="Path to .rrd file")
    p.add_argument("--entity", "-e", required=True, help="Entity path")
    p.add_argument("--threshold", "-t", type=float, default=1.0, help="Gap threshold in seconds")

    # at
    p = sub.add_parser("at", help="Query entity data at a time or relative to another entity")
    p.add_argument("rrd_path", help="Path to .rrd file")
    p.add_argument("--entity", "-e", required=True, help="Entity to query")
    p.add_argument("--time", help="Absolute timestamp (ISO format)")
    p.add_argument("--ref", dest="ref_entity", help="Reference entity for relative queries")
    p.add_argument("--ref-event", dest="ref_event", default="last", help="first or last (default: last)")
    p.add_argument("-n", type=int, default=1, help="Number of nearest rows to return")

    args = parser.parse_args()
    cmd_map = {
        "entities": cmd_entities,
        "schema": cmd_schema,
        "head": cmd_head,
        "tail": cmd_tail,
        "tf": cmd_tf,
        "info": cmd_info,
        "warnings": cmd_warnings,
        "rate": cmd_rate,
        "gaps": cmd_gaps,
        "at": cmd_at,
    }
    cmd_map[args.command](**vars(args))


if __name__ == "__main__":
    main()
