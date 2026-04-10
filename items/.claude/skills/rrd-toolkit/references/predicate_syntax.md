# Predicate Syntax

Predicates are expressions evaluated once per row. Used by `rrd-when` and `rrd-correlate`.

## Bindings per row

| Name | Meaning |
|---|---|
| `value` | The component value (single vector, or list of vectors for point clouds) |
| `translation`, `position`, `point` | Aliases for `value` |
| `size` | Number of top-level elements (e.g. number of points in a point cloud, 1 for a single vec3) |
| `shape` | numpy shape tuple |
| `x`, `y`, `z`, `w` | Individual components of a single vector (if length 2/3/4) |

## Allowed functions

`norm(v)`, `abs(v)`, `min(...)`, `max(...)`, `len(v)`, `sum(v)`.

## Allowed operators

Arithmetic: `+ - * / // % **`
Comparison: `< <= > >= == !=`
Logical: `and or not`
Subscript: `v[0]`, slice: `v[0:3]`
Containment: `x in [...]`

## Disallowed

Function calls other than the allowed ones. Attribute access. `exec`, `eval`, `import`.
Anything exotic is rejected by AST whitelist.

## Examples

### On a single vector (e.g. `Transform3D:translation`)
```
z < 0.5                         # height below 0.5m
norm(value - [0, 2, 6]) < 1.0   # within 1m of (0,2,6)
abs(x) < 0.1 and abs(y) < 0.1   # stationary in XY
```

### On a list of vectors (e.g. `Points3D:positions`)
```
size > 10000                    # point cloud with >10k points
size == 0                       # empty point cloud
shape[0] < 100                  # fewer than 100 elements
```

### On a scalar (e.g. `Scalar:scalar`)
```
value > 9.8
```
