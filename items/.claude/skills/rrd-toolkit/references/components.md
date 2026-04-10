# Common Rerun Components (Cheatsheet)

## Transforms
- `Transform3D:translation` — `[x, y, z]` (single vec3 per row)
- `Transform3D:quaternion` — `[qx, qy, qz, qw]` (single vec4 per row)
- `Transform3D:parent_frame` — string
- `Transform3D:child_frame` — string

## Points / point clouds
- `Points3D:positions` — N×3 array (N points)
- `Points3D:colors` — N×4 RGBA
- `Points3D:radii` — N floats

## Boxes
- `Boxes3D:centers` — N×3
- `Boxes3D:half_sizes` — N×3
- `Boxes3D:colors` — N×4

## Meshes
- `Mesh3D:vertex_positions` — N×3
- `Mesh3D:triangle_indices` — M×3 int
- `Mesh3D:vertex_colors` — N×4

## Line strips
- `LineStrips3D:positions` — list of polylines (list of vec3)

## Cameras
- `Pinhole:image_from_camera` — 3×3 intrinsics matrix
- `Pinhole:resolution` — `[width, height]`
- `Image:buffer` — raw pixels
- `EncodedImage:blob` — compressed pixels (e.g. PNG, JPEG)
- `DepthImage:data` — depth array

## Scalars / tensors
- `Scalar:scalar` — single float (for time series plots)
- `Tensor:data` — N-D array

## Text / logs
- `TextLog:text` — string
- `TextLog:level` — log level

## Archetype naming
Rerun column names are formatted `<Archetype>:<component>`. The **archetype** is the logical
bundle (e.g. `Transform3D`, `Points3D`). The **component** is the field (e.g. `translation`,
`positions`).

Full column key: `<entity_path>:<Archetype>:<component>` (e.g. `/world/odom:Transform3D:translation`).

When calling tools, `--component` takes the `<Archetype>:<component>` part.
