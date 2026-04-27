# Block Operations Tools (7)

Blocks are reusable named groups of entities. A **block definition** is the template; a **block reference** (INSERT entity) is a placed instance with position, scale, and rotation.

---

## block_list
No parameters. Returns all block definitions: `{name, origin, attribute_count, entity_count, is_xref, description}`.

## block_insert
Place a block reference in the drawing.

| Param | Type | Description |
|-------|------|-------------|
| `name` | `str` | Block definition name (must exist) |
| `x, y` | `float` | Insertion point |
| `x_scale` | `float` | X scale factor (default: 1.0) |
| `y_scale` | `float` | Y scale factor (default: 1.0) |
| `rotation` | `float` | Rotation in degrees (default: 0) |
| `layer` | `str \| null` | Target layer |

Returns entity info with handle (type: INSERT).

## block_explode
Decompose a block reference into individual entities.

| Param | Type | Description |
|-------|------|-------------|
| `handle` | `str` | Block reference (INSERT entity) handle |

Returns list of new entity handles created from explosion.

## block_get_attributes
Read attribute values from a block reference.

| Param | Type | Description |
|-------|------|-------------|
| `handle` | `str` | Block reference handle |

Returns `{tag: value}` dict of all attributes.

## block_set_attributes
Write attribute values to a block reference.

| Param | Type | Description |
|-------|------|-------------|
| `handle` | `str` | Block reference handle |
| `attributes` | `dict` | `{tag: value}` pairs to set |

## block_create_from_entities
Create a new block definition from existing entities.

| Param | Type | Description |
|-------|------|-------------|
| `name` | `str` | New block definition name |
| `handles` | `list[str]` | Entity handles to include |
| `base_x, base_y` | `float` | Block base/insertion point |

Entities are moved into the block definition.

## block_find_references
Find all INSERT entities that reference a specific block.

| Param | Type | Description |
|-------|------|-------------|
| `name` | `str` | Block definition name |

Returns list of block reference entity infos.
