# Space Types

Controlled vocabulary for `spatial_role`, `spatial_position`,
`spatial_scale` in the CKO Schema V1 Section 2.

## 1. spatial_role (categorical)

What the space is **for** at the time of observation.

| Value | Definition | Example |
| --- | --- | --- |
| `transit` | People pass through. | Plaza walkway, school corridor outside. |
| `gathering` | People stay and meet. | Piazza, courtyard. |
| `service_point` | People are served at a point. | Concierge desk, food kiosk area. |
| `contemplative` | People observe or reflect. | Garden, memorial. |
| `play` | Children engage actively. | Kindergarten playground. |
| `retail` | People shop or browse. | Mall atrium. |
| `waiting` | People queue or wait. | Station forecourt. |
| `working` | People labour or learn. | Outdoor classroom. |
| `mixed` | More than one role coexists. | School yard (play + working). |

A CKO picks one role. If two roles are coequal, use
`mixed` and add a `notes` field in evidence.

## 2. spatial_position (categorical)

Where the space sits in its **broader context**.

| Value | Definition | Example |
| --- | --- | --- |
| `open_ground` | Open at ground level. | Lawn, plaza. |
| `elevated` | Above grade. | Rooftop, terrace. |
| `enclosed` | Fully surrounded. | Atrium, courtyard. |
| `edge` | Boundary between two contexts. | Waterfront, treeline. |
| `island` | Surrounded by a different context. | Plaza island in a roadway. |
| `hidden` | Low visibility from outside. | Back garden, sunken courtyard. |
| `exposed` | High visibility from outside. | Stage, public sculpture site. |

## 3. spatial_scale (categorical)

The intervention "s footprint.

| Value | Range (m^2) | Typical |
| --- | --- | --- |
| `small` | `<200` | Backyard, single classroom zone. |
| `medium` | `200..1000` | Kindergarten courtyard. |
| `large` | `1000..5000` | Community park, school yard. |
| `vast` | `>=5000` | City park, masterplan segment. |

`spatial_scale` is not the same as `budget`. A small
spatial scale may have a large budget (a luxury villa).
A vast spatial scale may have a small budget (a public
park funded for one season).

## 4. environmental_relationship (free text)

Use one short phrase:

- `urban_infill` -- surrounded by city fabric.
- `urban_park` -- within city, but landscaped frame.
- `urban_waterfront` -- with water on one edge.
- `suburban` -- residential suburb.
- `rural` -- outside settlement.
- `forest` -- tree-covered.
- `wetland` -- water-covered or flood-prone.
- `coastal` -- sea or large lake.
- `mountain` -- sloped alpine or hillside.
- `indoor` -- fully roofed, conditioned space.
- `hybrid` -- partial indoor, partial outdoor.

The phrase is searchable. Always pick the **strongest**
descriptor; do not stack.

## Maintenance

- Adding a value to a category is a non-breaking change
  (allowed without ADR). Vocabulary is read by the future
  CKO Validator.
- Renaming a value is breaking and requires ADR.
- Removing a value still in use requires ADR.
