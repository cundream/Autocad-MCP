# Example: Apartment Floor Plan

Create a 3-room apartment: living room, bedroom, kitchen with doors and windows.

## Setup

```
drawing_new()
template_apply_layers("architectural")
# Creates: WALLS, DOORS, WINDOWS, DIMENSIONS, TEXT, FURNITURE, PLUMBING, HVAC
```

## Draw Exterior Walls (12m x 8m)

```
layer_set_current("WALLS")

# Exterior boundary
entity_create_rectangle(x1=0, y1=0, x2=12000, y2=8000)
```

## Draw Interior Walls

```
# Living/bedroom divider (vertical at x=5000)
entity_create_line(x1=5000, y1=0, x2=5000, y2=8000)

# Kitchen divider (horizontal at y=4000, from x=5000)
entity_create_line(x1=5000, y1=4000, x2=12000, y2=4000)
```

## Add Doors (0.9m openings)

```
layer_set_current("DOORS")

# Living room door (south wall)
entity_create_arc(cx=2000, cy=0, radius=900, start_angle=0, end_angle=90)

# Bedroom door (on divider wall)
entity_create_arc(cx=5000, cy=2000, radius=900, start_angle=90, end_angle=180)

# Kitchen door (on divider wall)
entity_create_arc(cx=7000, cy=4000, radius=900, start_angle=0, end_angle=90)
```

## Add Windows (1.5m wide)

```
layer_set_current("WINDOWS")

# Living room window (north wall)
entity_create_line(x1=1500, y1=8000, x2=3000, y2=8000, color=5)

# Bedroom window (east wall)
entity_create_line(x1=12000, y1=5500, x2=12000, y2=7000, color=5)

# Kitchen window (east wall)
entity_create_line(x1=12000, y1=1500, x2=12000, y2=3000, color=5)
```

## Add Dimensions

```
layer_set_current("DIMENSIONS")

# Overall width
dimension_linear(x1=0, y1=0, x2=12000, y2=0, dim_x=6000, dim_y=-800)

# Overall height
dimension_linear(x1=0, y1=0, x2=0, y2=8000, dim_x=-800, dim_y=4000)

# Room widths
dimension_linear(x1=0, y1=8000, x2=5000, y2=8000, dim_x=2500, dim_y=8500)
dimension_linear(x1=5000, y1=8000, x2=12000, y2=8000, dim_x=8500, dim_y=8500)
```

## Add Room Labels

```
layer_set_current("TEXT")

entity_create_text(text="LIVING ROOM", x=2500, y=4000, height=300)
entity_create_mtext(text="12.0 m²", x=2500, y=3500, width=2000, height=200)

entity_create_text(text="BEDROOM", x=8500, y=6000, height=300)
entity_create_mtext(text="28.0 m²", x=8500, y=5500, width=2000, height=200)

entity_create_text(text="KITCHEN", x=8500, y=2000, height=300)
entity_create_mtext(text="28.0 m²", x=8500, y=1500, width=2000, height=200)
```

## Verify

```
analysis_entity_stats()
analysis_layer_stats()
validation_check(["empty_layers", "zero_length"])
drawing_save("C:/drawings/apartment.dxf")
```
