# Layer Management Tools (12)

Layers organize entities by category (walls, doors, dimensions, etc.). Each layer has: name, color (ACI), linetype, lineweight, and states (on/off, frozen/thawed, locked/unlocked).

---

## layer_list
No parameters. Returns list of all layers with properties: `{name, color, linetype, lineweight, is_on, is_frozen, is_locked, is_current}`.

## layer_create
| Param | Type | Description |
|-------|------|-------------|
| `name` | `str` | New layer name |
| `color` | `int` | ACI color (default: 7=white) |
| `linetype` | `str` | Linetype name (default: `"Continuous"`) |

## layer_delete
| Param | Type | Description |
|-------|------|-------------|
| `name` | `str` | Layer to delete (must be empty, cannot be layer "0") |

## layer_set_current
| Param | Type | Description |
|-------|------|-------------|
| `name` | `str` | Layer to make current (new entities go here) |

## layer_modify
| Param | Type | Description |
|-------|------|-------------|
| `name` | `str` | Layer to modify |
| `color` | `int \| null` | New color |
| `linetype` | `str \| null` | New linetype |
| `lineweight` | `float \| null` | New lineweight |

## layer_freeze / layer_thaw
Freeze hides and excludes from regeneration (faster). Thaw restores.

| Param | Type | Description |
|-------|------|-------------|
| `name` | `str` | Layer name |

## layer_lock / layer_unlock
Lock prevents editing but keeps visible. Unlock restores editing.

| Param | Type | Description |
|-------|------|-------------|
| `name` | `str` | Layer name |

## layer_hide / layer_show
Hide turns layer off (invisible). Show turns it on.

| Param | Type | Description |
|-------|------|-------------|
| `name` | `str` | Layer name |

## layer_isolate
Shows only the specified layer, hides all others.

| Param | Type | Description |
|-------|------|-------------|
| `name` | `str` | Layer to keep visible |

To restore: `layer_show` each hidden layer, or reopen the drawing.
