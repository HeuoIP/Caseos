# 04 Positioning Method

> How a space is positioned in the user's mind and in the market.
> Positioning is not design. Positioning is the answer to the question
> "compared to what, and for whom?"

## 1. Purpose

Define one method for positioning a space so that the design choices,
the recommendation, and the user-facing explanation are coherent. A
space that is well-designed but poorly positioned will not be chosen.
A space that is well-positioned but poorly designed will disappoint.

## 2. Scope

**In scope**
- The four axes along which a space is positioned: story, user, place,
  and price.
- The relationship between positioning and the score vector in
  03_Value_Taxonomy.md.
- The way positioning changes the weight vector without changing the
  score vector.

**Out of scope**
- Brand identity systems, logos, and graphic design.
- Marketing-channel strategy.
- Sales process design.

## 3. Core Concepts

Positioning has four axes. Each space has a position on each axis; the
four positions together form the space's market posture.

1. **Story positioning** — what narrative the space is part of
   (e.g. "the first playground in the city designed with the new
   inclusive-design standard").
2. **User positioning** — which user group the space is *for* and,
   equally important, which it is *not for*.
3. **Place positioning** — how the space relates to its physical
   and cultural context (a landmark, a quiet corner, a connector).
4. **Price positioning** — the capex and opex tier relative to
   comparable spaces in the same market.

These four axes do not change the score vector of a candidate. They
change the **weight vector** the user applies to that score vector.
A well-positioned space asks the user to weight a different subset of
value dimensions than an unpositioned space.

## 4. Heuristics

- **Positioning is subtraction, not addition.** A space positioned as
  "for 3 to 6 year olds" is automatically a space that is not for 9 to
  12 year olds. Saying "yes" to one user means saying "no" to another.
- **The user who is excluded is as important as the user who is
  included.** A space that is "for everyone" is usually for no one.
- **Story positioning must be true.** A space cannot be positioned as
  "the most inclusive playground in the region" if it has three steps
  to the entrance.
- **Place positioning is local.** A landmark in a city centre is
  not a landmark in a forest.
- **Price positioning is comparative.** A space can be "premium" only
  relative to a peer set the user knows.

## 5. Vocabulary

- **Position** — the four-axis posture of a space.
- **Weight vector** — the tuple of value-dimension weights the user
  applies when scoring candidates.
- **Peer set** — the comparable spaces a user uses as a reference.
- **Subtraction** — the explicit decision of which users a space is
  not for.
- **Story arc** — the narrative a space participates in over time.

## 6. Common Pitfalls

- **Confusing positioning with marketing.** Marketing communicates a
  position; positioning is what makes a position defensible.
- **Positioning without subtraction.** "For everyone" is not a
  position.
- **Positioning that contradicts the score vector.** A "calm retreat"
  position with a thrill-equipment-heavy score vector will fail on
  first visit.
- **Letting the client override the position.** The client's wishes
  are inputs, not the position itself.

## 7. Cross-References

- 03_Value_Taxonomy.md — positioning changes the weight vector.
- 01_Space_Decision_Method.md — positioning is an input to the method.
- 07_Lifestyle_Model.md — the user axis of positioning is shaped by
  lifestyle.
- 02_Expert_Rules.md heuristic 1 (the photo lies) and 7 (theme is a
  wrapper) directly constrain how positioning is communicated.

## 8. Worked Example

**Space.** A 1500 m² community park in a second-tier Chinese city,
near a new residential development.

**Positioning decisions.**
- **Story.** "A second-home park for new families." Not a destination
  park, not a transit corridor.
- **User.** Children 0 to 9 and their caregivers. NOT teenagers, NOT
  serious athletes. The exclusion is explicit and welcome.
- **Place.** A quiet corner, not a landmark. The architecture is
  intentionally recessive; the planting does the talking.
- **Price.** Mid-tier. The capex is below the city's flagship park;
  the opex is below the median for community parks.

**Effect on the score vector.** A thrill-oriented candidate (e.g. a
large slide or a tall climbing tower) is rejected not because it
scores low, but because it does not match the position. The method
prefers a Reading_Corner, a small Treehouse, a low-height slide, and a
planting-rich landscape.

## 9. Open Questions

- [ ] Is positioning always an input, or can the engine propose one?
- [ ] How does positioning interact with multi-tenant sites (one
  space, multiple user groups)?
- [ ] How often should a space be re-positioned? Once at design, or
  every 3 to 5 years?
- [ ] Is there a "no-position" position, and is it ever the right
  answer?

## 10. Maintenance

- Positioning examples should accumulate as the benchmark set grows.
- A change to the four axes is a breaking change.
- Story positioning must always be cross-checked against the score
  vector of the recommended candidate; a contradiction is a flag
  for review, not a release blocker.
