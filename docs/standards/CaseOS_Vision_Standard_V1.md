# CaseOS Vision Standard V1



## 1. Vision Engine Role



## 2. Core Principles



## 3. Analysis Workflow



## 4. Theme Taxonomy

Theme = the **head** classification of a playground case
(e.g. is this case "Forest-themed" or "Pirate-themed"?).

### 4.1 Identifier Schema

Each theme has a stable ID of the form `<GROUP>.<LEAF>`. Both halves are
stored verbatim in JSON outputs.

- **9 groups:** NATURE, ANIMAL, OCEAN, SPACE, CASTLE, TRANSPORTATION,
  FANTASY, SCIENCE, TRADITIONAL_CULTURE.
- **41 leaves** in total. The full list lives in the library.

### 4.2 Theme Library (content lives in `knowledge/`)

The actual theme definitions live in `knowledge/taxonomy/theme/`. One MD
per leaf, named `<Label>.md` (spaces as underscores, e.g. `Deep_Sea.md`).

Each leaf MD has 11 fixed sections:

Story Core, Core Emotion, Learning Goal, Typical Color, Materials,
Landscape, Children Behavior, Storyline (5 stages), Design Language,
Engineering, Maintain.

See `knowledge/taxonomy/theme/Forest.md` as the canonical reference.

### 4.3 Multi-Theme Output Schema

A case may carry more than one theme. Always output **at least one**
theme per case.

Required shape:

```json
{
  "theme": [
    {"id": "NATURE.FOREST", "role": "primary",   "confidence": 0.92},
    {"id": "ANIMAL.WOLF",   "role": "secondary", "confidence": 0.61}
  ]
}
```

| Field | Rule |
| --- | --- |
| `id` | Stable ID `<GROUP>.<LEAF>` from the library. Never free text. |
| `role` | `"primary"` (exactly one) or `"secondary"` (zero to two). |
| `confidence` | Float, `0.0`–`1.0`. See calibration below. |

### 4.4 Selection Workflow

1. **Identify** — scan the image for visual cues (sculpted forms,
   signage text, color saturation, props, character imagery) and propose
   candidate IDs from any group.
2. **Pick primary** — the most dominant story / spatial cue. Exactly one.
3. **Pick secondary** — up to 2, only when at least one clear supporting
   cue exists and `confidence >= 0.5`.
4. **Calibrate confidence**:
   - `0.9–1.0`: multiple strong cues align (sculpted form + signage +
     color saturation all match the same leaf).
   - `0.7–0.9`: one strong cue plus supporting cues.
   - `0.5–0.7`: one cue, ambiguous backdrop.
   - below `0.5`: omit. Do not guess.
5. **Cross-check** — if the chosen `theme` contradicts visible evidence,
   lower confidence or omit.

### 4.5 Forbidden

- Free-text labels like `"forest"` or `"森林"`. Always use the stable ID.
- Picking a theme with no matching visual cue.
- Emitting two `primary` themes for one case.
- Mixing taxonomies: a `theme` is **not** a `play_behavior` or a `style`.

## 5. Style Taxonomy



## 6. Site Type Taxonomy



## 7. Age Group Taxonomy



## 8. Play Behavior Taxonomy



## 9. Functional Unit Taxonomy



## 10. Material Taxonomy



## 11. Color Taxonomy



## 12. Design Language Taxonomy



## 13. Spatial Layout Analysis



## 14. Storytelling Analysis



## 15. Landscape Integration



## 16. Engineering Feasibility



## 17. Commercial Value



## 18. Innovation Analysis



## 19. Maintenance Analysis



## 20. Output JSON Schema



## 21. Confidence Rules



## 22. Self Check Rules



## 23. Forbidden Rules



## 24. Prompt Version History

