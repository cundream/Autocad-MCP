# Dimension Tools (5)

All dimension tools return entity info with handle. Dimensions are placed on the current layer unless `layer` is specified.

---

## dimension_linear
Linear dimension between two points (horizontal or vertical measurement).

| Param | Type | Description |
|-------|------|-------------|
| `x1, y1` | `float` | First extension line origin |
| `x2, y2` | `float` | Second extension line origin |
| `dim_x, dim_y` | `float` | Dimension line position (controls placement) |
| `layer` | `str \| null` | Target layer |

## dimension_aligned
Aligned dimension — measures true distance between points regardless of angle.

| Param | Type | Description |
|-------|------|-------------|
| `x1, y1` | `float` | First point |
| `x2, y2` | `float` | Second point |
| `distance` | `float` | Offset distance for dimension line |
| `layer` | `str \| null` | Target layer |

## dimension_angular
Angular dimension between two lines meeting at a vertex.

| Param | Type | Description |
|-------|------|-------------|
| `vertex_x, vertex_y` | `float` | Angle vertex point |
| `start_x, start_y` | `float` | First line endpoint |
| `end_x, end_y` | `float` | Second line endpoint |
| `dim_x, dim_y` | `float` | Dimension arc position |
| `layer` | `str \| null` | Target layer |

## dimension_radius
Radius dimension for circles and arcs.

| Param | Type | Description |
|-------|------|-------------|
| `center_x, center_y` | `float` | Circle/arc center |
| `radius` | `float` | Radius value |
| `angle` | `float` | Leader angle in degrees (where arrow points) |
| `layer` | `str \| null` | Target layer |

## dimension_diameter
Diameter dimension across a circle.

| Param | Type | Description |
|-------|------|-------------|
| `x1, y1` | `float` | First point on diameter |
| `x2, y2` | `float` | Opposite point on diameter |
| `layer` | `str \| null` | Target layer |
