# Batch, Template & Validation Tools (5)

## Batch Operations

### entity_batch_create
Create multiple entities in a single call. Reports progress.

| Param | Type | Description |
|-------|------|-------------|
| `entities` | `list[dict]` | Entity definitions (see format below) |

Each dict requires `type` and type-specific params:

```json
[
  {"type": "line", "x1": 0, "y1": 0, "x2": 100, "y2": 0},
  {"type": "circle", "cx": 50, "cy": 50, "radius": 25},
  {"type": "text", "text": "Hello", "x": 10, "y": 10, "height": 5},
  {"type": "rectangle", "x1": 0, "y1": 0, "x2": 200, "y2": 100},
  {"type": "point", "x": 75, "y": 75},
  {"type": "arc", "cx": 50, "cy": 0, "radius": 10, "start_angle": 0, "end_angle": 180},
  {"type": "polyline", "points": [[0,0],[10,10],[20,0]], "closed": true}
]
```

Optional per-entity: `layer`, `color`, `linetype`.

Returns `{created: [...handles], errors: [...]}`. Partial success is possible.

### entity_batch_modify
Apply multiple modifications in a single call. Reports progress.

| Param | Type | Description |
|-------|------|-------------|
| `operations` | `list[dict]` | Operation definitions |

Each dict requires `handle` and `action`:

```json
[
  {"handle": "1A", "action": "move", "dx": 10, "dy": 20},
  {"handle": "2B", "action": "rotate", "base_x": 0, "base_y": 0, "angle_deg": 45},
  {"handle": "3C", "action": "scale", "base_x": 0, "base_y": 0, "factor": 2.0},
  {"handle": "4D", "action": "delete"},
  {"handle": "5E", "action": "set_properties", "layer": "WALLS", "color": 1}
]
```

Returns results per operation.

---

## Templates

### template_apply_layers
Apply a standard layer set to the current drawing.

| Param | Type | Description |
|-------|------|-------------|
| `template` | `str` | Template name: `architectural`, `mechanical`, `electrical`, `piping` |

Creates predefined layers with standard names, colors, and linetypes.

### template_list
No parameters. Returns all available templates and their layer definitions.

---

## Validation

### validation_check
Run quality checks on the drawing.

| Param | Type | Description |
|-------|------|-------------|
| `checks` | `list[str] \| null` | Check types (default: all) |

Available checks:
- `empty_layers` — Layers with no entities
- `zero_length` — Lines/arcs with zero length
- `duplicate_entities` — Overlapping identical entities

Returns `{issues: [{check, severity, message, details}, ...], summary}`.
