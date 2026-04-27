# Analysis Tools (9)

Tools for querying and measuring drawing contents.

---

## analysis_entity_stats
No parameters. Returns entity counts grouped by type and by layer.

```json
{
  "total": 150,
  "by_type": {"LINE": 50, "CIRCLE": 20, "TEXT": 30, ...},
  "by_layer": {"WALLS": 40, "DOORS": 10, ...}
}
```

## analysis_find_in_region
Find entities within a rectangular region.

| Param | Type | Description |
|-------|------|-------------|
| `x1, y1` | `float` | Region minimum corner |
| `x2, y2` | `float` | Region maximum corner |
| `type_filter` | `str \| null` | Filter by entity type |

Returns list of entity infos within the bounding box.

## analysis_measure_distance
Measure distance between two points.

| Param | Type | Description |
|-------|------|-------------|
| `x1, y1` | `float` | Point 1 |
| `x2, y2` | `float` | Point 2 |

Returns `{distance, dx, dy, angle}`.

## analysis_measure_area
Calculate area of a polygon.

| Param | Type | Description |
|-------|------|-------------|
| `points` | `list[list[float]]` | Polygon vertices (min 3 points) |

Returns `{area, perimeter, centroid}`.

## analysis_bounding_box
No parameters. Returns `{min_x, min_y, max_x, max_y, width, height}` for all entities.

## analysis_select_by_layer
Get all entities on a specific layer.

| Param | Type | Description |
|-------|------|-------------|
| `layer_name` | `str` | Layer to select from |

Returns list of entity infos.

## analysis_select_by_type
Get all entities of a specific type.

| Param | Type | Description |
|-------|------|-------------|
| `entity_type` | `str` | Type: LINE, CIRCLE, ARC, LWPOLYLINE, TEXT, MTEXT, INSERT, HATCH, SPLINE, ELLIPSE |

Returns list of entity infos.

## analysis_layer_stats
No parameters. Returns per-layer statistics: entity count, types present, color, state.

## analysis_entities_in_region
Alias/variant of `analysis_find_in_region` — check both for availability.
