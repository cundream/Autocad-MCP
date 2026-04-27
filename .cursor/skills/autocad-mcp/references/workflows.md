# Common Workflows

## 1. New Drawing from Scratch

```
Progress:
- [ ] Step 1: Create drawing
- [ ] Step 2: Set up layers
- [ ] Step 3: Draw entities
- [ ] Step 4: Add dimensions
- [ ] Step 5: Add text annotations
- [ ] Step 6: Verify and save
```

**Step 1**: `drawing_new()` — creates empty drawing

**Step 2**: Create layers for organization:
```
layer_create("WALLS", color=7, linetype="Continuous")
layer_create("DOORS", color=3)
layer_create("WINDOWS", color=5)
layer_create("DIMENSIONS", color=1)
layer_create("TEXT", color=2)
```
Or use `template_apply_layers("architectural")` for standard sets.

**Step 3**: Draw geometry on appropriate layers:
```
layer_set_current("WALLS")
entity_create_rectangle(x1=0, y1=0, x2=6000, y2=4000)
entity_create_line(x1=3000, y1=0, x2=3000, y2=4000)
```

**Step 4**: Add dimensions:
```
layer_set_current("DIMENSIONS")
dimension_linear(x1=0, y1=0, x2=6000, y2=0, dim_x=3000, dim_y=-500)
```

**Step 5**: Add text labels:
```
layer_set_current("TEXT")
entity_create_text(text="Living Room", x=1500, y=2000, height=200)
```

**Step 6**: Verify and save:
```
analysis_entity_stats()     # check entity counts
validation_check()          # run quality checks
drawing_save("/path/to/drawing.dxf")
```

---

## 2. Edit Existing DXF

```
Progress:
- [ ] Step 1: Open file
- [ ] Step 2: Explore contents
- [ ] Step 3: Make changes (with transaction)
- [ ] Step 4: Verify and save
```

**Step 1**: `drawing_open("/path/to/file.dxf")`

**Step 2**: Explore:
```
analysis_entity_stats()                      # overview
layer_list()                                 # see layers
entity_list(type_filter="LINE", limit=20)    # browse entities
```

**Step 3**: Begin transaction, then modify:
```
transaction_begin()
entity_move(handle="1A2B", dx=100, dy=0)
entity_set_properties(handle="3C4D", color=1, layer="WALLS")
entity_delete(handle="5E6F")
transaction_commit()    # or transaction_rollback() to undo all
```

**Step 4**: `drawing_save()`

---

## 3. Batch Entity Creation

```
Progress:
- [ ] Step 1: Prepare entity list
- [ ] Step 2: Batch create
- [ ] Step 3: Verify results
```

**Step 1**: Build entity definitions:
```json
[
  {"type": "line", "x1": 0, "y1": 0, "x2": 100, "y2": 0, "layer": "WALLS"},
  {"type": "line", "x1": 100, "y1": 0, "x2": 100, "y2": 100, "layer": "WALLS"},
  {"type": "circle", "cx": 50, "cy": 50, "radius": 10, "layer": "DETAILS"},
  {"type": "text", "text": "A1", "x": 50, "y": -20, "height": 5, "layer": "TEXT"}
]
```

**Step 2**: `entity_batch_create(entities=[...])` — returns handles for all created entities

**Step 3**: `analysis_entity_stats()` to verify counts

---

## 4. Drawing Analysis

```
Progress:
- [ ] Step 1: Open drawing
- [ ] Step 2: Get overview stats
- [ ] Step 3: Examine specific areas
- [ ] Step 4: Measure and report
```

**Step 1**: `drawing_open(path)` or `drawing_info()` if already open

**Step 2**:
```
analysis_entity_stats()    # by type and layer
analysis_layer_stats()     # per-layer details
analysis_bounding_box()    # drawing extents
```

**Step 3**: Region queries:
```
analysis_find_in_region(x1=0, y1=0, x2=1000, y2=1000, type_filter="LINE")
analysis_select_by_layer(layer_name="WALLS")
analysis_select_by_type(entity_type="CIRCLE")
```

**Step 4**: Measurements:
```
analysis_measure_distance(x1=0, y1=0, x2=100, y2=100)
analysis_measure_area(points=[[0,0],[100,0],[100,100],[0,100]])
```

---

## 5. Template-Based Drawing

```
Progress:
- [ ] Step 1: Create drawing with template
- [ ] Step 2: Apply layer standards
- [ ] Step 3: Add content
- [ ] Step 4: Validate and save
```

**Step 1**: `drawing_new(template="/path/to/template.dwt")` (or `drawing_new()` without template)

**Step 2**: `template_apply_layers("architectural")` — creates standard layers

**Step 3**: Draw content on appropriate layers

**Step 4**:
```
validation_check(["empty_layers", "zero_length"])
drawing_save("/path/to/output.dxf")
```
