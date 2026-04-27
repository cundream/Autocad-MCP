# Example: Basic Room Drawing

Create a simple room with walls, a door opening, dimensions, and labels.

## Setup

```
drawing_new()
layer_create("WALLS", color=7)
layer_create("DOORS", color=3)
layer_create("DIMENSIONS", color=1)
layer_create("TEXT", color=2)
```

## Draw Walls (5m x 4m room)

```
layer_set_current("WALLS")

# Outer walls as rectangle
entity_create_rectangle(x1=0, y1=0, x2=5000, y2=4000)
# Returns: {handle: "A1", type: "LWPOLYLINE", ...}
```

## Add Door Opening (0.9m wide on south wall)

```
layer_set_current("DOORS")

# Door opening represented as an arc (90° swing)
entity_create_arc(cx=2000, cy=0, radius=900, start_angle=0, end_angle=90)
# Returns: {handle: "B2", type: "ARC", ...}

# Door frame lines
entity_create_line(x1=2000, y1=0, x2=2000, y2=100)
entity_create_line(x1=2900, y1=0, x2=2900, y2=100)
```

## Add Dimensions

```
layer_set_current("DIMENSIONS")

# Room width
dimension_linear(x1=0, y1=0, x2=5000, y2=0, dim_x=2500, dim_y=-500)

# Room height
dimension_linear(x1=5000, y1=0, x2=5000, y2=4000, dim_x=5500, dim_y=2000)

# Door width
dimension_linear(x1=2000, y1=0, x2=2900, y2=0, dim_x=2450, dim_y=-300)
```

## Add Labels

```
layer_set_current("TEXT")
entity_create_text(text="BEDROOM", x=2500, y=2000, height=200)
entity_create_text(text="5000", x=2500, y=-800, height=150)
```

## Verify and Save

```
analysis_entity_stats()
# Expected: ~8 entities across 4 layers

validation_check(["empty_layers"])
# Should report no issues

drawing_save("C:/drawings/room.dxf")
```
