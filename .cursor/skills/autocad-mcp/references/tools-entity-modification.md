# Entity Modification & Query Tools (13)

All modify tools require a `handle` (hex string). Get handles from `entity_list()` or any `entity_create_*` return value.

---

## Modification Tools (10)

### entity_move
| Param | Type | Description |
|-------|------|-------------|
| `handle` | `str` | Entity handle |
| `dx, dy` | `float` | Displacement vector |

### entity_copy
Returns new entity info with a **new handle**.

| Param | Type | Description |
|-------|------|-------------|
| `handle` | `str` | Entity to copy |
| `dx, dy` | `float` | Offset for the copy |

### entity_rotate
| Param | Type | Description |
|-------|------|-------------|
| `handle` | `str` | Entity handle |
| `base_x, base_y` | `float` | Rotation base point |
| `angle_degrees` | `float` | Rotation angle (CCW) |

### entity_scale
| Param | Type | Description |
|-------|------|-------------|
| `handle` | `str` | Entity handle |
| `base_x, base_y` | `float` | Scale base point |
| `factor` | `float` | Scale factor |

### entity_mirror
| Param | Type | Description |
|-------|------|-------------|
| `handle` | `str` | Entity handle |
| `x1, y1` | `float` | Mirror line point 1 |
| `x2, y2` | `float` | Mirror line point 2 |

### entity_offset
Works on line, circle, polyline.

| Param | Type | Description |
|-------|------|-------------|
| `handle` | `str` | Entity handle |
| `distance` | `float` | Offset distance (positive = outward) |

### entity_delete
| Param | Type | Description |
|-------|------|-------------|
| `handle` | `str` | Entity to delete |

### entity_array_rectangular
| Param | Type | Description |
|-------|------|-------------|
| `handle` | `str` | Entity to array |
| `rows` | `int` | Number of rows |
| `cols` | `int` | Number of columns |
| `row_spacing` | `float` | Row spacing |
| `col_spacing` | `float` | Column spacing |

Returns list of new entity handles.

### entity_array_polar
| Param | Type | Description |
|-------|------|-------------|
| `handle` | `str` | Entity to array |
| `center_x, center_y` | `float` | Array center point |
| `count` | `int` | Number of copies |
| `angle` | `float` | Total angle to fill (degrees, default: 360) |

### entity_set_properties
| Param | Type | Description |
|-------|------|-------------|
| `handle` | `str` | Entity handle |
| `layer` | `str \| null` | Move to layer |
| `color` | `int \| null` | Change ACI color |
| `linetype` | `str \| null` | Change linetype |
| `lineweight` | `float \| null` | Change lineweight |

All property params are optional — only provided ones are changed.

---

## Query Tools (3)

### entity_get
| Param | Type | Description |
|-------|------|-------------|
| `handle` | `str` | Entity handle |

Returns full entity info: `{handle, type, layer, color, linetype, visible, properties}`.

### entity_list
| Param | Type | Description |
|-------|------|-------------|
| `type_filter` | `str \| null` | Filter: `LINE`, `CIRCLE`, `ARC`, `LWPOLYLINE`, `TEXT`, `MTEXT`, `INSERT`, `HATCH`, etc. |
| `layer_filter` | `str \| null` | Filter by layer name |
| `limit` | `int` | Max results (default: 100) |
| `offset` | `int` | Skip first N results (default: 0) |

### entity_delete_many
| Param | Type | Description |
|-------|------|-------------|
| `handles` | `list[str]` | List of handles to delete |

Reports progress. Returns `{deleted, failed, errors}`.
