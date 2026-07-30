# Diagnosis Types

Controlled vocabulary for `problem_type` in the CKO Schema
V1 Section 4.

A diagnosis is **why a case works or fails**. The
vocabulary is split into three families so a CKO can be
retrieved by polarity:

- **positive** -- the case illustrates a successful move.
- **negative** -- the case illustrates a failure or
  cautionary pattern.
- **edge** -- the case is a borderline or hybrid (good in
  one segment, weak in another).

## Positive

| Value | Definition |
| --- | --- |
| `positive_strong_anchor` | The case has one clear, repeatable anchor and the rest of the design supports it. |
| `positive_coherent_language` | The case unifies one material or pattern across the site with no competing cores. |
| `positive_experience_depth` | The case invites repeat visitation through challenge, cooperation, or exploration (DR-003 inverted). |
| `positive_amplify_strengths` | The case takes an existing site feature and amplifies it without fanfare (Constitution P004). |
| `positive_spatial_fitness` | The case "s scale and proportion match its user segment (e.g., child-scale for kindergarten). |
| `positive_throughline` | The case carries one story from arrival to departure. |

## Negative

| Value | Definition |
| --- | --- |
| `negative_no_anchor` | The case has no spatial anchor and reads as a collection (DR-001). |
| `negative_competing_cores` | The case has multiple competing anchors; nothing wins. |
| `negative_style_conflict` | The case mixes material / colour / motif languages without intent (DR-002). |
| `negative_scale_mismatch` | The case "s scale / proportion fails the user segment. |
| `negative_decoration_without_story` | The case has visual richness without narrative (CR-003 default failure). |
| `negative_visual_not_play` | The case photographs well but children leave (DR-003). |
| `negative_resource_misallocation` | The case over-spends on a single object; surrounds empty (RR-001). |
| `negative_undefined_problem` | The case tries to solve an unclear brief (CR-001 failure). |

## Edge

| Value | Definition |
| --- | --- |
| `edge_photo_vs_dwell` | Strong photo, weak dwell. |
| `edge_iconic_vs_usable` | Iconic landmark; ordinary usability. |
| `edge_loved_by_adults_only` | Adults love it; children do not. |
| `edge_peak_only` | Great at one time of day or one season; weak otherwise. |
| `edge_context_bound` | Works in its original context; would fail elsewhere. |
| `edge_trend_dependent` | Reads as fresh today; ages fast. |

## Use

A CKO picks one `problem_type`. If the case illustrates
two problems coequally, pick the **primary** and put the
secondary in `diagnosis` prose.

The polarity is part of the retrieval contract:

- `positive_*` CKOs are surfaced when the Decision Engine
  needs a "what good looks like" reference.
- `negative_*` CKOs are surfaced when Diagnosis flags a
  matching defect (e.g., DR-001 fires; the
  Recommendation layer cites `negative_no_anchor` CKOs).
- `edge_*` CKOs are surfaced when the Brain needs nuance
  ("this works but watch out for X").

## Maintenance

- Adding a value: allowed without ADR.
- Renaming a value: breaking, requires ADR.
- Removing a value still in use: breaking, requires ADR.
- Moving a value between families (positive / negative /
  edge) is also a breaking change.
