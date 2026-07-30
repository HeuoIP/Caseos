# Space Character Record -- <image_id>

> One MD per case. Use this template as a working scratch-pad for both
> AI pre-fill and human review. When the row reaches consensus, the
> structured fields become entries in knowledge/space_character/dataset/.

---

# Basic Information

- **Image ID:** <image_id>
- **Space Type:** <SITE.PUBLIC_PARK | SITE.KINDERGARTEN | SITE.COMMERCIAL | SITE.COMMUNITY | SITE.RESIDENTIAL | ...>
- **Location:** <city / district / address>
- **Area:** <m^2>
- **Notes:** <free-form context, anything that does not fit the structured fields>

---

# AI Analysis

> Filled by the AI pre-annotation pass. Human reviewer reads these
> sections and either agrees, corrects, or rewrites them.

## Space Character

One short paragraph describing what the space FEELS like to be in.
Use sensory and experiential language. Avoid marketing words
(striking, amazing, iconic, world-class). Avoid AI jargon.

Examples (do NOT copy verbatim -- these are only structural):

- "Open, sunlit, low-slung. Movement along a wide central axis; edges soft with grass and seating."
- "Enclosed, layered, child-scale. Wood and rope dominate; the eye keeps being pulled up."
- "Commercial but warm. The play area is visible from the atrium; families pass by and stop."

## Space Strength

Bullet list of physical / contextual strengths the space ALREADY has.

- <strength 1>
- <strength 2>
- <strength 3>

## Space Weakness

Bullet list of physical / contextual weaknesses or constraints.

- <weakness 1>
- <weakness 2>

## Space Potential

What this space COULD become. Written as one or two concrete moves,
not as a wish list.

- <potential 1>
- <potential 2>

## Core Atmosphere

One sentence. The dominant emotional register a child (or adult)
would feel inside this space. Example: "curious and grounded."

---

# Human Review

> A human reviewer (designer, project manager, or domain expert)
> reads the AI analysis above and decides what stays, what changes,
> and what gets dropped.

- **Reviewer:** <name / role>
- **Date:** <YYYY-MM-DD>
- **Agreement Score (1-5):** <1 = total rewrite needed, 5 = ship as-is>
- **Comments:**
  - <free-form observation 1>
  - <free-form observation 2>
- **Corrections:**
  - <field> -> <corrected value or sentence>
  - <field> -> <corrected value or sentence>

---

# Final Consensus

> The fields below are what gets promoted into the structured dataset
> (knowledge/space_character/dataset/<image_id>.yaml). They are the
> only fields that downstream CaseOS agents consume.

- **Approved Space Character:** <one paragraph, max 80 words>
- **Approved Potential:** <one or two concrete moves, max 60 words>
- **Approved Priority:** <HIGH | MEDIUM | LOW>
- **Approved Reviewer:** <name>
- **Approved Date:** <YYYY-MM-DD>

---

# Versioning

- **Template Version:** v1
- **Schema Reference:** CaseOS_Space_Character_Schema_V1 (see docs/standards/)
- **Next Review Cadence:** quarterly
