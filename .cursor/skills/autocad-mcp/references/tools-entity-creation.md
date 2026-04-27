# Entity Creation Tools (13)

All creation tools return `{handle, type, layer, color, linetype, visible, properties}`. The `handle` (hex string) is required for all subsequent operations on that entity.

Common optional params on all creation tools:

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `layer` | `str` | Current layer | Target layer name |
| `color` | `int` | 256 (ByLayer) | ACI color (1-255, 256=ByLayer, 0=ByBlock) |
| `linetype` | `str` | `"ByLayer"` | Linetype name |

---

## entity_create_line
| Param | Type | Description |
|-------|------|-------------|
| `x1, y1` | `float` | Start point |
| `x2, y2` | `float` | End point |

## entity_create_circle
| Param | Type | Description |
|-------|------|-------------|
| `cx, cy` | `float` | Center point |
| `radius` | `float` | Radius |

## entity_create_arc
| Param | Type | Description |
|-------|------|-------------|
| `cx, cy` | `float` | Center point |
| `radius` | `float` | Radius |
| `start_angle` | `float` | Start angle (degrees, CCW from X) |
| `end_angle` | `float` | End angle (degrees) |

## entity_create_polyline
| Param | Type | Description |
|-------|------|-------------|
| `points` | `list[list[float]]` | `[[x,y], [x,y], ...]` coordinate pairs |
| `closed` | `bool` | Close the polyline (default: false) |

## entity_create_rectangle
| Param | Type | Description |
|-------|------|-------------|
| `x1, y1` | `float` | First corner |
| `x2, y2` | `float` | Opposite corner |

Creates an LWPOLYLINE (closed).

## entity_create_text
| Param | Type | Description |
|-------|------|-------------|
| `text` | `str` | Text content |
| `x, y` | `float` | Insertion point |
| `height` | `float` | Text height (default: 2.5) |
| `rotation` | `float` | Rotation angle in degrees (default: 0) |

## entity_create_mtext
| Param | Type | Description |
|-------|------|-------------|
| `text` | `str` | Content (`\P` for paragraph break, `{\H...;}` for formatting) |
| `x, y` | `float` | Insertion point |
| `width` | `float` | Text box width (default: 100) |
| `height` | `float` | Character height (default: 2.5) |

## entity_create_hatch
| Param | Type | Description |
|-------|------|-------------|
| `pattern` | `str` | Pattern name: `SOLID`, `ANSI31`, `ANSI32`, `STEEL`, `GRAVEL`, etc. |
| `boundary_points` | `list[list[float]]` | Closed boundary polygon `[[x,y], ...]` |
| `scale` | `float` | Pattern scale (default: 1.0) |
| `angle` | `float` | Pattern angle (default: 0) |

## entity_create_spline
| Param | Type | Description |
|-------|------|-------------|
| `fit_points` | `list[list[float]]` | Points the spline passes through |

## entity_create_ellipse
| Param | Type | Description |
|-------|------|-------------|
| `cx, cy` | `float` | Center point |
| `major_axis_x, major_axis_y` | `float` | Major axis endpoint (relative to center) |
| `ratio` | `float` | Minor/major axis ratio (0.0–1.0) |

## entity_create_point
| Param | Type | Description |
|-------|------|-------------|
| `x, y` | `float` | Point coordinates |

## entity_create_block_ref
| Param | Type | Description |
|-------|------|-------------|
| `name` | `str` | Block definition name (must exist) |
| `x, y` | `float` | Insertion point |
| `x_scale, y_scale` | `float` | Scale factors (default: 1.0) |
| `rotation` | `float` | Rotation in degrees (default: 0) |
