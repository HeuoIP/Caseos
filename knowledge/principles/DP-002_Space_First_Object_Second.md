# DP-002: Space First, Object Second

- **ID:** DP-002
- **Status:** Accepted
- **Date:** 2026-07-30
- **Layer:** Knowledge (Design Principle)
- **Companion documents:**
  - `knowledge/decision_rules/Space_Decision_Principles.md` -- top-level principles
  - `docs/standards/CaseOS_Constitution_V1.md` -- philosophy
  - `docs/standards/CaseOS_Decision_Principles_V1.md` -- implementation guide

---

## 1. Statement

> Examine the space -- its dimensions, light, climate, surroundings,
> existing features, constraints, opportunities, and atmosphere --
> BEFORE suggesting any object.
> The same object produces different outcomes in different spaces.
> A space can be enhanced, neutral, or ruined by an object.
> Only the first outcome is acceptable.

## 2. Why this principle exists

- Constitution Principle 003 -- *Understand before recommending.
  Observe before judging. Think before generating.* The "observe"
  step is the space examination that DP-002 requires.
- Constitution Principle 004 -- *Amplify the strengths of a space.
  Do not cover up the weaknesses with random objects.* Amplifying
  is impossible without first observing the strengths.
- Decision Principle 002 -- *Space before Object.* The space is
  examined before any object is named.

This principle exists because CaseOS has repeatedly seen
recommendations that look correct on paper (good catalogue,
recognised vendor, attractive images) and yet produce the wrong
outcome on site because the space was never examined.

## 3. What it means

The "space" here is the entire physical, environmental, and
contextual envelope of the target site, not just the empty plot.
At minimum, the space is examined across five axes, in this order:

1. **Dimensions and geometry.** Size, shape, slope, vertical
   clearance, sightlines, approach, and edges. A 1.5 m slide is
   a feature in a 200 m² garden and a liability in a 30 m²
   courtyard.
2. **Light and climate.** Sun path, prevailing wind, rain
   exposure, humidity, temperature range. A wooden bench in
   full equatorial sun fails in two seasons; a steel bench in
   the same spot lasts decades.
3. **Surroundings and context.** Adjacent land use, neighbours,
   noise, view, traffic, vegetation, microclimate. A "quiet
   reading corner" by a busy road is not quiet.
4. **Existing features.** Trees, water, structures, services,
   utilities, drainage, paving, soil. A space already has assets
   and constraints; the recommendation works with both, not
   against them.
5. **Atmosphere.** The felt sense of the place -- quiet, lively,
   formal, intimate, exposed, sheltered. Atmosphere is the
   attribute most often missed by catalogue-driven design.

Three direct consequences:

1. **No object is ever proposed first.** Object candidates are
   only admitted after the five axes are filled in. If a user
   asks "what slide should I buy?", the engine answers the space
   questions first.
2. **The space record is part of the output.** The recommendation
   includes a short Space Summary that names the five axes and
   the verdict on each. The recommendation is reproducible only
   if the Space Summary is reproducible.
3. **The same object, two spaces, two verdicts.** A "treehouse"
   in a woodland is a fit. A "treehouse" on a rooftop is a
   contradiction in terms. The engine does not pick the object
   and then look for a space to justify it.

## 4. When to apply

Apply DP-002 at every one of the following moments:

- Before the first object candidate is admitted to the
  recommendation set.
- Whenever the user proposes an object before describing the
  space.
- Whenever the candidate set is dominated by a single vendor
  or single theme (the engine has likely skipped the space step).
- Whenever the Space Summary is missing from a recommendation
  output.
- Whenever two recommendation sets for similar sites diverge
  unexpectedly -- the divergence usually means one of them did
  not do the space step honestly.

## 5. When NOT to apply

DP-002 yields in three well-defined situations:

1. **The space is already known and recorded.** Re-running the
   five-axis observation on a recorded space is wasted effort;
   the engine should reuse the Space Summary unless the user
   says the space has changed.
2. **The user has only one axis confirmed and refuses to
   provide the others.** The engine records the known axis and
   asks for the rest. It does NOT proceed to objects.
3. **The object is a placeholder for a future observation.**
   During the early product flow (Sprint 8), the user uploads
   a single photo. The engine records what the photo shows,
   marks the unseen axes as unknown, and proceeds with explicit
   unknowns. This is not a violation of DP-002; it is DP-002
   executed honestly under information scarcity.

## 6. Failure modes

When DP-002 is ignored, four predictable failures occur.

1. **Catalogue style leakage.** The recommendation looks like
   a vendor "s product line, because the vendor "s objects are
   the only ones that survive the candidate set. The space has
   not constrained the candidates at all.
2. **Theme-as-substitute-for-place.** A "Forest theme" is applied
   to a flat urban rooftop, producing a stylised forest in the
   sky that has nothing to do with the actual site. The space
   has been replaced by a theme.
3. **Wrong-scale objects.** A slide sized for a 200 m² site is
   proposed for a 20 m² site, or a small bench for a 2 000 m²
   plaza. The dimensions axis was skipped.
4. **Climate-blind objects.** Wooden objects in tropical rain,
   metal objects in salty coastal air, fabric objects in
   equatorial sun. The climate axis was skipped.

## 7. Worked example

**Target space.** A 60 m² urban balcony on the 14th floor of a
residential tower, west-facing, summer afternoon sun, no shade,
strong prevailing wind from the south-west, view of a busy
intersection.

**Without DP-002.** A supplier proposes a "cosy outdoor lounge":
wicker sofa set, fire pit, planters, decorative lighting. The
balcony becomes unusable in summer afternoons (heat, glare) and
unsafe in winter winds (light furniture blows around).

**With DP-002.**

- Dimensions: 60 m² rectangle, 1.2 m wide access door, low
  parapet (1.05 m). Furniture must be narrow and able to pass
  through the door.
- Light / climate: 4-6 hours of direct west sun in summer,
  strong south-west wind, no fixed shading.
- Surroundings: view of a busy intersection, audible traffic.
- Existing features: a single water tap, a power outlet, a
  small drainage grate.
- Atmosphere: exposed, urban, transient.

Recommendation: a heavy timber bench fixed to the parapet (wind-
proof), a retractable sail-shade on the west side, two tall
planters doubling as wind-screens (bamboo or similar), warm-tone
indirect lighting, a small noise-buffering water feature at the
parapet edge. No fire pit. No wicker. No decorative-only items.

Outcome: every element answers an axis. The recommendation is
defensible.

## 8. Cross-references

- **Constitution P003** -- Understand before recommending.
- **Constitution P004** -- Amplify the strengths.
- **Decision Principle 002** -- Space before Object.
- **Space_Decision_Principles.md** -- principle 1
  (*Evidence before invention*) and principle 2
  (*Hard constraints are not negotiable*).
- **Expert Handbook 01 Method**, step 1 (Five-axis space
  observation) and step 3 (Hard-constraint filter). DP-002 is
  the knowledge that step 1 operationalises.
- **Expert Handbook 06 Space Psychology** -- atmosphere is a
  space attribute, not a decoration attribute.
- **ADR-005 Decision Intelligence** -- the Space Agent is the
  runtime expression of DP-002.

## 9. Maintenance

- A change to DP-002 (e.g. a new axis, or a re-ordering of the
  five axes) is a breaking change to the Space Agent and to
  every recommendation that has cited a Space Summary.
- The five axes are not exhaustive. A new axis (e.g.
  *acoustics*, *smell*, *seasonal use pattern*) may be added
  by appending, not by replacing. Versioned.
- DP-002 does not prescribe how to record a space; the Schema
  layer (`schemas/`) owns the recording shape.
