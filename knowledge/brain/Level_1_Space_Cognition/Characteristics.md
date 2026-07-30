# Characteristics -- Space Cognition

- **Layer:** Brain -- Level 1
- **Status:** Accepted
- **Date:** 2026-07-30
- **Companion documents:** `Role.md`, `Position.md`,
  `Emotion.md`, `README.md`.

## Statement

> Space Cognition captures a space across **nine observable
> characteristics**, grouped into four families.
> Every characteristic is **observed, not judged**.
> Every characteristic carries **provenance**.

## The four families

| Family | What it describes | Characteristics |
| --- | --- | --- |
| **Physical** | The space as a physical object. | Geometry, Light & Climate, Existing Features |
| **Contextual** | The space in relation to its surroundings. | Surroundings |
| **Experiential** | The space as it is felt. | Atmosphere, Sensory |
| **Spatial Structure** | How the space organizes movement and time. | Flow, Rhythm, Boundaries |

Each characteristic is described by:
- a **state** (one of a controlled vocabulary),
- a **provenance** flag (`observed` / `inferred` / `unknown`),
- a **source** link back to the V3 JSON field that supports it,
- an optional **note** explaining an inference or unknown.

## Provenance rules

Three flags, mutually exclusive for any single characteristic:

| Flag | Meaning | Example |
| --- | --- | --- |
| `observed` | Directly visible in the input (Vision JSON, user-stated facts). | "Geometry: rectangular, 30 m x 20 m" (visible from site plan). |
| `inferred` | Deduced from related observations; the inference is recorded. | "Atmosphere: sheltered (inferred from the surrounding hedge height visible in the image)." |
| `unknown` | Not observable from the current input; the unknown is surfaced. | "Light: unknown (the photo is taken at dusk; sun path cannot be inferred)." |

A characteristic without provenance is **fabrication**. The
Diagnosis Layer (Level 2) and downstream layers are forbidden
from using an unprovenanced characteristic.

## The nine characteristics

### 1. Geometry (Physical)

The physical shape of the space: size, footprint, slope, vertical
clearance, edges, and access points.

**Vocabulary (non-exhaustive):**

- **Shape:** rectangular / square / circular / irregular / linear /
  wedge / L-shaped.
- **Size band:** intimate (< 50 m2) / small (50-200 m2) / medium
  (200-1000 m2) / large (1000-10000 m2) / vast (> 10000 m2).
- **Slope:** flat / gentle (< 5%) / moderate (5-15%) / steep (> 15%).
- **Vertical clearance:** low (< 3 m) / standard (3-10 m) / open
  (> 10 m, e.g. outdoor plaza).
- **Access count:** one / two / many.

### 2. Light & Climate (Physical)

The space "s exposure to natural light and weather.

**Vocabulary (non-exhaustive):**

- **Sun exposure:** full sun / partial sun / mostly shaded / fully
  shaded.
- **Prevailing wind:** sheltered / moderate / exposed.
- **Climate band:** tropical / temperate / arid / cold / alpine /
  coastal.
- **Seasonal use:** year-round / spring-autumn / summer-only /
  winter-only / indoor-controlled.

### 3. Existing Features (Physical)

The assets already on the site: vegetation, water, structures,
services, paving, soil.

**Vocabulary (non-exhaustive):**

- **Vegetation:** mature trees / young trees / shrubs / lawn /
  wild / bare.
- **Water:** none / stream / pond / fountain / pool / sea-adjacent.
- **Structures:** none / pavilion / pergola / wall / building /
  play equipment (existing).
- **Services:** electricity / water / drainage / irrigation /
  Wi-Fi.
- **Ground:** paving / grass / sand / gravel / wood deck / mixed.

### 4. Surroundings (Contextual)

The space "s relation to adjacent land use, neighbours, view,
traffic, and noise.

**Vocabulary (non-exhaustive):**

- **Adjacent land use:** residential / commercial / institutional /
  industrial / natural / mixed.
- **View:** open / framed / enclosed / blocked.
- **Noise:** quiet / moderate / noisy / traffic-dominated.
- **Neighbour interaction:** private / semi-public / public.

### 5. Atmosphere (Experiential)

The **observable condition** that produces the felt sense of the
place. Atmosphere is the **observable**, not the felt response.
The felt response is recorded separately under `Emotion.md`.

**Vocabulary (non-exhaustive):**

- **Density of activity:** empty / sparse / moderate / busy /
  crowded.
- **Visible users:** none / children / adults / mixed / staff-only.
- **Activity types visible:** quiet / play / transit / service /
  ceremony.
- **Time signature:** timeless / morning / midday / afternoon /
  evening / night-active.

### 6. Sensory (Experiential)

The non-visual sensory qualities: what the space **sounds like**,
**smells like**, **feels like** to touch.

**Vocabulary (non-exhaustive):**

- **Sound:** silent / rustling / running water / traffic /
  mechanical / music / voices / mixed.
- **Smell:** neutral / vegetal / water / food / chemical / city /
  marked.
- **Touch underfoot:** soft / hard / uneven / smooth / mixed.
- **Temperature feel:** cool / neutral / warm.

### 7. Flow (Spatial Structure)

How a person moves through the space.

**Vocabulary (non-exhaustive):**

- **Path structure:** single / linear / loop / radial / network /
  maze / free.
- **Direction:** one-way / two-way / multi-directional.
- **Speed affordance:** walking only / slow mixed / mixed traffic.
- **Wayfinding:** obvious / moderate / confusing / none needed.

### 8. Rhythm (Spatial Structure)

How the space repeats or varies: the cadence of elements.

**Vocabulary (non-exhaustive):**

- **Repetition:** none / regular grid / grouped clusters / varied.
- **Surprise moments:** none / occasional / frequent.
- **Scale variation:** uniform / varied / dramatic.
- **Visual noise:** quiet / moderate / busy / chaotic.

### 9. Boundaries (Spatial Structure)

How the space is enclosed, opened, or marked off from its
surroundings.

**Vocabulary (non-exhaustive):**

- **Enclosure:** none (open) / low hedge / wall / change of level /
  change of material / change of light.
- **Threshold:** abrupt / graduated / porous.
- **Edge clarity:** undefined / soft / hard / architecturally
  defined.

## What Characteristics is NOT

- **Not a score.** The vocabulary is categorical, not numeric.
  Diagnosis may score, but Level 1 does not.
- **Not exhaustive.** New vocabulary may be added by future
  Sprints. Additions do not require ADR; renames do.
- **Not overlapping with Emotion.** Atmosphere is observable;
  Emotion is the predicted human response. The two are recorded
  separately.

## Cross-references

- `Role.md` -- the discipline of observation over judgment.
- `Position.md` -- where this output feeds in the pipeline.
- `Emotion.md` -- the related-but-separate emotional record.
- `knowledge/decision_model/Context_Model.md` Section 3 -- the
  runtime shape of these characteristics as the `space` sub-model.
- `knowledge/expert_handbook/06_Space_Psychology.md` -- the
  psychology research behind the vocabulary.

## Maintenance

- Adding a new **vocabulary term** to an existing characteristic
  is a non-breaking change (allowed without ADR).
- Adding a new **characteristic** is a breaking change (the
  Diagnosis Layer "s input contract grows) and requires ADR.
- Renaming or removing a **vocabulary term** is a breaking change
  and requires ADR.
- Renaming or removing a **characteristic** is a breaking change
  and requires ADR.
