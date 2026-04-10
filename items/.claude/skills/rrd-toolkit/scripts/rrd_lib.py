"""Shared helpers for rrd-toolkit CLI tools.

Loads .rrd files via rerun-sdk's Server + DataFusion, extracts arrow/pandas
dataframes per entity, provides timeline resolution, safe predicate eval,
and nearest-time lookup.
"""
from __future__ import annotations

import ast
import json
import math
import os
import sys
import warnings
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Dependency check + auto re-exec into a Python with the right deps
# ---------------------------------------------------------------------------

_VENV_CANDIDATES = [
    os.path.expanduser("~/repos/dimos/.venv/bin/python"),
    os.path.expanduser("~/repos/dimos2/.venv/bin/python"),
    os.path.expanduser("~/repos/dimos3/.venv/bin/python"),
    os.path.expanduser("~/repos/dimos4/.venv/bin/python"),
    os.path.expanduser("~/repos/dimos5/.venv/bin/python"),
    os.path.expanduser("~/repos/dimensional-applications/.venv/bin/python"),
]


def _reexec_if_needed() -> None:
    """Re-exec into a Python that has rerun + datafusion + numpy + pandas if current one doesn't."""
    if os.environ.get("RRD_TOOLKIT_REEXECED"):
        return
    try:
        import rerun  # noqa: F401
        import datafusion  # noqa: F401
        import numpy  # noqa: F401
        import pandas  # noqa: F401
        return  # current python is fine
    except ImportError:
        pass
    import subprocess
    override = os.environ.get("RRD_PYTHON")
    candidates = [override] if override else []
    candidates += _VENV_CANDIDATES
    for py in candidates:
        if not py or not os.path.exists(py):
            continue
        try:
            r = subprocess.run(
                [py, "-c", "import rerun, datafusion, numpy, pandas"],
                capture_output=True, timeout=10,
            )
            if r.returncode == 0:
                new_env = dict(os.environ, RRD_TOOLKIT_REEXECED="1")
                os.execve(py, [py] + sys.argv, new_env)
        except Exception:
            continue
    print(
        "ERROR: No Python found with rerun-sdk[datafusion], numpy, and pandas.\n"
        "Set RRD_PYTHON=/path/to/venv/bin/python or install:\n"
        "  uv pip install 'rerun-sdk[datafusion]' numpy pandas",
        file=sys.stderr,
    )
    sys.exit(2)


# Run at import time so every tool gets the right Python
_reexec_if_needed()


def _require_rerun() -> Any:
    import rerun as rr
    return rr

# ---------------------------------------------------------------------------
# Server / dataset loading
# ---------------------------------------------------------------------------

@contextmanager
def open_rrd(path: str):
    """Open an .rrd file and yield (server, dataset). Server shuts down on exit."""
    rr = _require_rerun()
    abs_path = str(Path(path).expanduser().resolve())
    if not os.path.exists(abs_path):
        print(f"ERROR: file not found: {abs_path}", file=sys.stderr)
        sys.exit(2)
    with rr.server.Server(port=None, datasets={"rec": [abs_path]}) as server:
        client = server.client()
        dataset = client.get_dataset("rec")
        yield server, dataset

# ---------------------------------------------------------------------------
# Schema enumeration
# ---------------------------------------------------------------------------

def enumerate_columns(dataset) -> dict[str, Any]:
    """Return a dict with index_columns, component_columns, entities."""
    schema = dataset.schema()
    index_cols = []
    component_cols = []
    entities: dict[str, dict] = {}

    for col in schema.index_columns():
        index_cols.append({"name": col.name, "is_static": col.is_static})

    for col in schema.component_columns():
        comp = {
            "name": col.name,
            "entity_path": col.entity_path,
            "archetype": str(col.archetype).replace("rerun.archetypes.", ""),
            "component": col.component,
            "component_type": str(col.component_type).replace("rerun.components.", ""),
            "is_static": col.is_static,
        }
        component_cols.append(comp)
        e = col.entity_path
        if e not in entities:
            entities[e] = {"components": [], "archetypes": set()}
        entities[e]["components"].append(col.component)
        entities[e]["archetypes"].add(comp["archetype"])

    # Convert sets to sorted lists
    for e in entities.values():
        e["archetypes"] = sorted(e["archetypes"])
        e["components"] = sorted(set(e["components"]))

    return {
        "index_columns": index_cols,
        "component_columns": component_cols,
        "entities": entities,
    }

def pick_timeline(index_cols: list[dict], preferred: str | None = None) -> str:
    """Pick a sensible default timeline."""
    names = [c["name"] for c in index_cols]
    if preferred and preferred in names:
        return preferred
    for pref in ("log_time", "frame_nr", "log_tick"):
        if pref in names:
            return pref
    if names:
        return names[0]
    raise RuntimeError("No timelines found in recording.")

# ---------------------------------------------------------------------------
# Data reading
# ---------------------------------------------------------------------------

def read_entity(
    dataset,
    entity_path: str,
    timeline: str | None = None,
    fill_latest_at: bool = False,
):
    """Return a pandas DataFrame of the given entity on the given timeline.

    Raises ValueError if the entity path is not present in the recording.
    """
    info = enumerate_columns(dataset)
    if entity_path not in info["entities"]:
        known = sorted(info["entities"].keys())
        print(
            f"ERROR: entity '{entity_path}' not found in recording.\n"
            f"Known entities ({len(known)}):\n" + "\n".join(f"  {e}" for e in known),
            file=sys.stderr,
        )
        sys.exit(2)
    tl = pick_timeline(info["index_columns"], timeline)
    view = dataset.filter_contents(entity_path)
    reader = view.reader(index=tl, fill_latest_at=fill_latest_at)
    arrow_tbl = reader.to_arrow_table()
    df = arrow_tbl.to_pandas()
    # Keep only the requested entity's data columns (filter_contents is lenient)
    keep = {"rerun_segment_id", tl}
    # also keep other index columns
    for c in info["index_columns"]:
        keep.add(c["name"])
    for c in df.columns:
        if c.startswith(entity_path + ":"):
            keep.add(c)
    df = df[[c for c in df.columns if c in keep]]
    return df, tl

def component_column_name(df, entity_path: str, component: str) -> str | None:
    """Return the pandas column name for a given entity:component, or None."""
    target = f"{entity_path}:{component}"
    for c in df.columns:
        if c == target:
            return c
    # Fallback: allow match on component only
    for c in df.columns:
        if c.endswith(f":{component}"):
            return c
    return None

# ---------------------------------------------------------------------------
# Time helpers
# ---------------------------------------------------------------------------

def to_timeline_seconds(series, timeline: str):
    """Convert a pandas timeline series to seconds (float)."""
    import pandas as pd
    if pd.api.types.is_datetime64_any_dtype(series):
        return (series.astype("int64") / 1e9)
    # integer counters (log_tick, frame_nr) — treat as seconds equivalent only if named 'log_tick'
    return series.astype("float64")

def nearest_index(times_sec, target_sec: float) -> int:
    """Return index of nearest value in sorted series."""
    import numpy as np
    arr = np.asarray(times_sec)
    idx = int(np.searchsorted(arr, target_sec))
    if idx <= 0:
        return 0
    if idx >= len(arr):
        return len(arr) - 1
    if abs(arr[idx] - target_sec) < abs(arr[idx - 1] - target_sec):
        return idx
    return idx - 1

# ---------------------------------------------------------------------------
# Component value extraction
# ---------------------------------------------------------------------------

def extract_values(series):
    """Unwrap a pandas series of list-of-fixed-size-list into a list of lists or arrays.

    Rerun stores components as list<fixed_size_list<T>> per row, e.g.
    Transform3D:translation -> [[x,y,z]] (list containing one vec3).
    This returns a python list where each element is either a list (single element)
    or a list of lists (multiple elements per row, e.g. point clouds).
    """
    result = []
    for val in series:
        if val is None:
            result.append(None)
            continue
        # val is typically a numpy array or list of arrays
        try:
            inner = list(val)
        except TypeError:
            result.append(val)
            continue
        if len(inner) == 0:
            result.append([])
        elif len(inner) == 1:
            # Single sub-element: unwrap one layer -> e.g. [x, y, z]
            elem = inner[0]
            if isinstance(elem, (str, bytes)):
                result.append(elem)
            else:
                try:
                    result.append(list(elem))
                except TypeError:
                    result.append(elem)
        else:
            # Multiple sub-elements (e.g. point cloud with N points)
            result.append([
                (x if isinstance(x, (str, bytes)) else (list(x) if hasattr(x, "__iter__") else x))
                for x in inner
            ])
    return result

def value_size(val) -> int:
    """Return length of a value (for point clouds: number of points)."""
    if val is None:
        return 0
    if isinstance(val, (list, tuple)):
        if len(val) == 0:
            return 0
        # If first element is itself iterable (list of lists), return top-level count
        first = val[0]
        if isinstance(first, (list, tuple)):
            return len(val)
        return 1  # single vector = 1 element
    return 1

# ---------------------------------------------------------------------------
# Safe predicate evaluator
# ---------------------------------------------------------------------------

_ALLOWED_NODES = (
    ast.Expression, ast.BoolOp, ast.BinOp, ast.UnaryOp, ast.Compare,
    ast.Name, ast.Load, ast.Constant, ast.List, ast.Tuple, ast.Call,
    ast.Subscript, ast.Index, ast.Slice, ast.Attribute,
    ast.And, ast.Or, ast.Not, ast.USub, ast.UAdd,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow, ast.FloorDiv,
    ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
)

_ALLOWED_FUNCS = {"norm", "abs", "min", "max", "len", "sum"}

def _norm(v):
    import numpy as np
    a = np.asarray(v, dtype=float).ravel()
    return float(math.sqrt((a * a).sum()))

def make_safe_env(value, size: int) -> dict[str, Any]:
    """Build a safe evaluation environment for a single row."""
    import numpy as np
    # Convert to numpy array so arithmetic works naturally in predicates.
    np_val = None
    if value is not None:
        try:
            np_val = np.asarray(value, dtype=float)
        except Exception:
            np_val = None
    env = {
        "size": size,
        "shape": tuple(np_val.shape) if np_val is not None else (),
        "norm": _norm,
        "abs": abs,
        "min": min,
        "max": max,
        "len": len,
        "sum": sum,
    }
    # Expose the numpy-ified value under multiple aliases.
    env["value"] = np_val if np_val is not None else value
    env["translation"] = env["value"]
    env["position"] = env["value"]
    env["point"] = env["value"]
    if np_val is not None:
        flat = np_val.ravel()
        if len(flat) >= 3:
            env["x"], env["y"], env["z"] = float(flat[0]), float(flat[1]), float(flat[2])
        elif len(flat) == 2:
            env["x"], env["y"] = float(flat[0]), float(flat[1])
        if len(flat) >= 4:
            env["w"] = float(flat[3])
    return env

def compile_predicate(expr: str):
    """Parse + validate + compile a predicate expression."""
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as e:
        raise ValueError(f"invalid predicate syntax: {e}") from e

    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED_NODES):
            raise ValueError(f"predicate contains disallowed syntax: {type(node).__name__}")
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in _ALLOWED_FUNCS:
                raise ValueError(
                    f"predicate calls unknown function: "
                    f"{ast.dump(node.func)} (allowed: {sorted(_ALLOWED_FUNCS)})"
                )
    return compile(tree, "<predicate>", "eval")

def eval_predicate(code, value, size: int) -> bool:
    env = make_safe_env(value, size)
    try:
        return bool(eval(code, {"__builtins__": {}}, env))
    except Exception:
        return False

# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def emit_json(obj: Any) -> None:
    """Print JSON to stdout with reasonable formatting. Replaces NaN/Inf with None."""
    import numpy as np

    def _clean(o):
        if isinstance(o, float):
            if o != o or o in (float("inf"), float("-inf")):
                return None
            return o
        if isinstance(o, (np.floating,)):
            f = float(o)
            if f != f or f in (float("inf"), float("-inf")):
                return None
            return f
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, np.ndarray):
            return [_clean(x) for x in o.tolist()]
        if isinstance(o, dict):
            return {k: _clean(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [_clean(x) for x in o]
        if isinstance(o, set):
            return sorted(_clean(x) for x in o)
        if hasattr(o, "isoformat"):
            return o.isoformat()
        return o

    cleaned = _clean(obj)

    class _Enc(json.JSONEncoder):
        def default(self, o):
            return str(o)

    json.dump(cleaned, sys.stdout, indent=2, cls=_Enc, allow_nan=False)
    sys.stdout.write("\n")

def timestamp_to_iso(ts) -> str:
    if ts is None:
        return ""
    if hasattr(ts, "isoformat"):
        return ts.isoformat()
    return str(ts)
