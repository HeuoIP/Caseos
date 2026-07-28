# CaseOS Object Library

This directory holds the **object / intervention** knowledge layer for the future Space Decision Engine. It is **content only**; no runtime decision engine is implemented yet. The Decision Engine will reason from these files together with the theme knowledge in `knowledge/taxonomy/theme/` and the rules in `knowledge/decision_rules/`.

Each object is one MD file. The library currently covers five starter objects spanning the future product surface (playground, urban, cultural, commercial). The library will grow.

## Why objects are a separate layer

- **Standards** define behavior.
- **Knowledge** provides content. Objects are content.
- **Schemas** define data shape.

Objects are not schemas, and they are not runtime rules. They are the content the future Decision Engine will retrieve when it needs to reason about what could be placed in a target space.

## Per-Object File Schema (unified template)

Every object MD follows the same 11 sections so the Decision Engine can rely on a consistent structure:

1. **Definition** — what the object is, in one paragraph.
2. **Spatial Requirements** — footprint, vertical clearance, clear zone.
3. **Capacity & User Fit** — typical capacity, age range, group configuration, adult accompaniment.
4. **Materials & Construction** — primary and secondary materials, construction type, lifespan, climate suitability.
5. **Safety & Standards** — applicable standards, critical risks, required safety surface, inclusive design considerations.
6. **Behavior Affordances** — primary and secondary behaviors, social configuration, sensory profile.
7. **Cost & Lifecycle** — indicative cost band, installation complexity, maintenance cycle, replacement cycle, spare part availability.
8. **Suitable Space Contexts** — best site types, climate/exposure fit, surrounding intensity, companion infrastructure.
9. **Theme Affinities** — strong fit, possible fit, themes to avoid, cultural/contextual notes.
10. **Adjacent Object Relationships** — pairs well with, conflicts with, replaces, replaced by.
11. **Decision Notes** — when to recommend, when NOT to recommend, open questions for the Decision Engine, last reviewed.

See `Treehouse.md` as the canonical reference for the template.

## Identifier Convention

- **Stable ID form:** `OBJECT.<LEAF>` in UPPER_SNAKE.
- **Label:** bilingual English（中文）, mirroring the theme taxonomy style.
- **Frontmatter:** the first blockquote carries the `Object ID`, `Label`, `Category`, and `Domain Affinity`. The Decision Engine can parse this block for fast filtering.

## Starter Library

| Object | Stable ID | Category | Domain Affinity |
| --- | --- | --- | --- |
| [`Treehouse`](Treehouse.md) | `OBJECT.TREEHOUSE` | STRUCTURE / ELEVATED_PLATFORM | PLAYGROUND, NATURE_PLAY, ECO_RESORT, EDUCATIONAL |
| [`Slide`](Slide.md) | `OBJECT.SLIDE` | MOVEMENT / DESCENT | PLAYGROUND, WATER_PLAY, ADVENTURE, COMMERCIAL_FAMILY_VENUE |
| [`Reading_Corner`](Reading_Corner.md) | `OBJECT.READING_CORNER` | REST / STORYTELLING / INCLUSION | PLAYGROUND, EDUCATION, COMMUNITY, TRADITIONAL_CULTURE |
| [`Interactive_Wall`](Interactive_Wall.md) | `OBJECT.INTERACTIVE_WALL` | ENGAGEMENT / MULTI_SENSORY / INCLUSION | EDUCATION, MUSEUM, SCIENCE, PLAYGROUND, INDOOR_FAMILY_VENUE |
| [`IP_Sculpture`](IP_Sculpture.md) | `OBJECT.IP_SCULPTURE` | LANDMARK / BRANDING / THEME_ANCHOR | PLAYGROUND, COMMERCIAL, THEME_PARK, PUBLIC_ART, REAL_ESTATE_MARKETING |

**Total entries:** 5

## Relationship to Other Knowledge

- **Theme leaves** (`knowledge/taxonomy/theme/`) now carry three new sections: `Recommended Objects`, `Unsuitable Objects`, `Alternative Objects`. Those sections reference the `OBJECT.<ID>` stable IDs defined here.
- **Decision rules** (`knowledge/decision_rules/Space_Decision_Principles.md`) define the principles the future Decision Engine will follow when reasoning across themes, objects, and user constraints.

## Open Questions for the Future

- [ ] Should cost bands be normalised to a single currency? To a purchasing-power index?
- [ ] Should objects be versioned (e.g. `OBJECT.TREEHOUSE.v2`)? Or treated as evergreen?
- [ ] When the same object exists in multiple domain packs (e.g. a treehouse in playground vs. eco-resort), do we need a domain-affinity weight?
- [ ] How do we represent the user-requirement dimension (budget band, climate zone, accessibility) inside this library?
