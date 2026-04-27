# Example: Flange with Bolt Pattern

Create a circular flange plate with bolt holes using polar array.

## Setup

```
drawing_new()
template_apply_layers("mechanical")
# Creates: OUTLINE, CENTERLINE, HIDDEN, DIMENSIONS, NOTES, SECTION, DETAIL
```

## Draw Flange Outline

```
layer_set_current("OUTLINE")

# Outer flange circle (diameter 200mm)
entity_create_circle(cx=0, cy=0, radius=100)
# Returns: {handle: "F1", ...}

# Inner bore (diameter 50mm)
entity_create_circle(cx=0, cy=0, radius=25)
# Returns: {handle: "F2", ...}
```

## Add Centerlines

```
layer_set_current("CENTERLINE")

# Horizontal centerline
entity_create_line(x1=-120, y1=0, x2=120, y2=0, linetype="CENTER")

# Vertical centerline
entity_create_line(x1=0, y1=-120, x2=0, y2=120, linetype="CENTER")
```

## Create Bolt Hole Pattern

```
layer_set_current("OUTLINE")

# First bolt hole on bolt circle (PCD = 150mm diameter, so radius = 75mm)
entity_create_circle(cx=75, cy=0, radius=6)
# Returns: {handle: "B1", ...}

# Create polar array: 6 holes evenly spaced
entity_array_polar(handle="B1", center_x=0, center_y=0, count=6, angle=360)
# Returns: list of 5 new handles (original + 5 copies = 6 total)
```

## Add Dimensions

```
layer_set_current("DIMENSIONS")

# Outer diameter
dimension_diameter(x1=-100, y1=0, x2=100, y2=0)

# Inner bore diameter
dimension_diameter(x1=-25, y1=0, x2=25, y2=0)

# Bolt circle diameter
dimension_radius(center_x=0, center_y=0, radius=75, angle=45)

# Bolt hole diameter
dimension_diameter(x1=69, y1=0, x2=81, y2=0)
```

## Add Notes

```
layer_set_current("NOTES")

entity_create_mtext(
    text="FLANGE PLATE\P6x M12 HOLES ON PCD 150\PMATERIAL: SS304",
    x=-120, y=-140,
    width=240, height=5
)
```

## Create Block from Bolt Hole

```
# Select all bolt hole entities and create a reusable block
# (Get handles from the array result)
block_create_from_entities(
    name="BOLT_PATTERN_6x150",
    handles=["B1", ...],  # all bolt hole handles
    base_x=0, base_y=0
)
```

## Verify

```
analysis_entity_stats()
# Expected: circles, lines, dimensions, mtext

analysis_bounding_box()
# Expected: approximately -120 to 120 in both axes

drawing_save("C:/drawings/flange.dxf")
```
