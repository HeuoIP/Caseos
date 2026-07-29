# 08 Object Value Map

> How the five starter objects in `knowledge/objects/` map to the
> seven value dimensions in 03_Value_Taxonomy.md. The map is the
> bridge that lets the engine score a candidate's value vector.

## 1. Purpose

Translate object descriptions into the value vocabulary, so the
Decision Engine can score and compare candidates. Without this map,
the object library is a catalogue; with it, the library becomes a
scoring surface.

## 2. Scope

**In scope**
- A scoring matrix from each starter object to each value
  dimension.
- Notes on why a score is what it is.
- Notes on which sub-dimensions drive the score.

**Out of scope**
- New object definitions (those live in `knowledge/objects/`).
- Per-site adjustments (those are the engine's job at runtime).

## 3. Core Concepts

The map is a 5 x 7 matrix: five starter objects, seven value
dimensions. Each cell is a score in the range 0.0 to 1.0, with a
short justification.

The seven value dimensions (from 03_Value_Taxonomy.md) are:
**Functional, Emotional, Social, Educational, Aesthetic,
Ecological, Economic.**

The five starter objects (from `knowledge/objects/`) are:
**Treehouse, Slide, Reading_Corner, Interactive_Wall, IP_Sculpture.**

A score is not absolute. It is the typical contribution of the
object to that dimension in a typical installation. Real scores
will vary by site, by scale, and by execution.

## 4. Heuristics

- **A score is a default, not a verdict.** The engine must be
  able to override the default score with site-specific evidence.
- **Score the object, not the design.** A Treehouse can be
  beautiful or ugly; the value map is about the object class,
  not the design.
- **Score the contribution, not the absolute value.** An
  Interactive_Wall is high on educational value, not because
  every wall teaches, but because the object class is oriented
  toward teaching.
- **Visible trade-offs are the point.** If a candidate scores
  high on emotional and low on ecological, that is a fact the
  user must see.

## 5. Vocabulary

- **Value vector** — the tuple of dimension scores for a
  candidate.
- **Default score** — the typical contribution of an object
  class to a value dimension.
- **Site override** — the engine's runtime adjustment of a
  default score based on site evidence.
- **Sub-dimension driver** — the sub-dimension that explains
  most of an object's score on a value dimension.

## 6. Common Pitfalls

- **Confusing the default score with a recommendation.** A
  high score does not mean "recommend this"; it means "this is
  what this object typically contributes."
- **Ignoring combinations.** A Reading_Corner plus an IP_Sculpture
  is not the sum of their value vectors; the combination has
  emergent properties (a sense of place) that neither has alone.
- **Letting one object dominate the score vector.** A space
  should be a portfolio; one object should not carry the entire
  value claim.

## 7. Cross-References

- 03_Value_Taxonomy.md — the seven value dimensions.
- `knowledge/objects/` — the object definitions and per-object
  detail.
- 01_Space_Decision_Method.md — how the engine aggregates the
  value vector.
- 06_Space_Psychology.md — the basis for emotional and social
  scores.

## 8. Worked Example

**Scoring matrix (default, typical installation).**

| Object | Func | Emot | Soci | Educ | Aest | Ecol | Econ |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Treehouse | 0.6 | 0.8 | 0.5 | 0.6 | 0.7 | 0.7 | 0.5 |
| Slide | 0.7 | 0.7 | 0.4 | 0.5 | 0.6 | 0.5 | 0.7 |
| Reading_Corner | 0.4 | 0.6 | 0.8 | 0.7 | 0.6 | 0.8 | 0.9 |
| Interactive_Wall | 0.5 | 0.6 | 0.8 | 0.9 | 0.4 | 0.3 | 0.4 |
| IP_Sculpture | 0.3 | 0.8 | 0.5 | 0.4 | 0.9 | 0.5 | 0.4 |

**Reading.**
- The Reading_Corner has the strongest inclusion story (high
  social, high ecological, high economic).
- The Interactive_Wall is the educational engine of the library
  (0.9) but expensive in ecological terms (0.3).
- The IP_Sculpture is the strongest aesthetic and emotional
  anchor (0.9, 0.8) but weak on functional value.
- The Treehouse is the most balanced object — no extreme lows,
  several highs.
- The Slide is the most economical movement object but weak on
  social value (parallel play, not cooperative).

**Trade-off example.** A user that weights educational + social
over ecological + cost will see the Interactive_Wall as the top
candidate. A user that weights ecological + cost will see the
Reading_Corner as the top candidate. Neither is wrong; the value
map makes the trade-off explicit.

## 9. Open Questions

- [ ] Should the matrix be expanded with sub-dimension scores?
- [ ] How are combinations of objects scored? Pairwise, or with
  a separate "combined" row?
- [ ] How does the matrix localise? Are there cultural adjustments
  to default scores?
- [ ] How is the matrix updated when a new object is added?

## 10. Maintenance

- The matrix is the source of truth for default value vectors.
  It must be updated when an object is added or revised.
- Score changes require an ADR.
- Worked examples accumulate; a new dimension is added only when
  a real case demonstrates its necessity.
