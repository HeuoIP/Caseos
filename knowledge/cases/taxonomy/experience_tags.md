# Experience Tags

Controlled vocabulary for `atmosphere`, `emotional_response`,
`child_behavior`, and supporting experience fields in the
CKO Schema V1 Section 3.

This vocabulary maps onto the **seven Experience
Perception axes** in
`knowledge/brain/experience_perception/README.md`. CKOs
carry axis readings as searchable tags.

## 1. atmosphere (single dominant mood)

One word. Allowed values:

- `quiet`
- `lively`
- `ceremonial`
- `playful`
- `tense`
- `neutral`
- `warm`
- `cold`
- `magical`
- `industrial`

The CKO adds one sentence in `atmosphere` after the tag
to give context; the tag alone is the searchable handle.

## 2. emotional_response (multi-population list)

Allowed values per population:

### Universal

- `wonder`
- `safety`
- `shelter`
- `exposure`
- `discovery`
- `lostness`
- `mystery`
- `home`
- `work`
- `play`

### Child-leaning

- `adventure`
- `den`
- `hide_and_seek`
- `show_off`
- `cooperation`
- `challenge`
- `pretend`

### Adult-leaning

- `retreat`
- `memory`
- `familiarity`
- `anticipation`
- `belonging`

A CKO picks 1-3 values per population segment. The
default population is "child"; if the CKO is
multi-population, list each segment "s response separately
in `notes` (but the searchable tags stay universal).

## 3. child_behavior (list)

Allowed values:

- `running`
- `climbing`
- `sliding`
- `swinging`
- `balancing`
- `hiding`
- `building`
- `observing`
- `socialising`
- `imagining`
- `resting`
- `navigating`

These are **designed-for** behaviours; the CKO records
what the design invites, not what every child does.

## 4. interaction_type (single enum)

| Value | Definition |
| --- | --- |
| `passive` | The body and the space do not co-act (a sculpture garden). |
| `light` | Touch or short dwell is invited but optional. |
| `active` | Movement is invited; some skill is required. |
| `social` | Multi-person co-action is the primary mode. |

A CKO "s `interaction_type` must be the **dominant**
mode. Mixed-mode projects use `social` if co-action
dominates; else `active`.

## 5. stay_value (single enum)

| Value | Definition |
| --- | --- |
| `low` | Pass-through or short visit. |
| `mid` | Re-visit a few times per week. |
| `high` | Anchor of a regular routine. |

## Why mirror Experience Perception axes

The Brain "s seven axes (scale_proportion, spatial_
relationship, atmosphere, story_feeling, imagination,
stay_desire, vitality) are full multi-dimensional
records. CKOs only carry the searchable handles
(atmosphere, child_behavior, stay_value). The remaining
axes are derived at Retrieval Engine time from the
Brain "s vocabulary if needed.

This keeps CKOs **lean** (retrievable) while the Brain
remains **rich** (decision-grade).

## Use

A CKO Section 3 must include all five fields. The
enumerated fields (atmosphere, interaction_type,
stay_value) use the values above. Free-text fields
(emotional_response, child_behavior) use the **tag**
values where possible; one short note is allowed per
field.

## Maintenance

- Adding a tag (anywhere): non-breaking, allowed without
  ADR.
- Renaming a tag: breaking (CKOs may cite the old).
- Removing a tag still in use: breaking.
- Changing the dominant-mood vocabulary (`atmosphere`):
  breaking, requires ADR.
