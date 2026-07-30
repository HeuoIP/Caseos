# Project Types

Controlled vocabulary for `case_identity.project_type` in
the CKO Schema V1 Section 0.

This vocabulary mirrors the **commercial segments** listed
in `docs/product/Product.md` Section 2 ("Target Users").
If the Product team adds a segment, this file gains one
leaf in the same sprint.

## Values

| Value | Definition | Typical user |
| --- | --- | --- |
| `kindergarten` | Education for children 2-6. | Director, head teacher. |
| `school` | K-12 or specialty school. | Principal, facility manager. |
| `real_estate_residential` | Property developer, residential. | Developer, sales. |
| `real_estate_commercial` | Office / mixed-use developer. | Developer, asset manager. |
| `malls_retail` | Shopping centre, retail plaza. | Centre manager. |
| `hospitality_hotel` | Hotel, resort. | GM, experience lead. |
| `hospitality_restaurant` | Restaurant, cafe chain. | Owner / F&B lead. |
| `cultural_tourism` | Museum, scenic area, heritage site. | Curator, operator. |
| `community_public` | Community centre, library. | Council, programme lead. |
| `public_park` | City park, waterfront park. | Park authority. |
| `commercial_experiential` | Brand-led flagship space, pop-up. | Brand director. |
| `family_residential` | Single family (villa, townhouse). | Owner. |
| `design_firm_internal` | Firm "s own R&D / portfolio study. | Designer. |
| `other` | None of the above. | -- |

`design_firm_internal` covers CKOs that exist primarily as
reference material for designers rather than a delivered
project.

## Mappings

Many projects cross categories. Use this priority:

1. The **client "s primary business segment**.
2. If ambiguous, the **funding source** segment.
3. If still ambiguous, use `mixed` and add the conflicting
   segments to `applicable_conditions` instead.

`mixed` is intentionally not a value here. CKOs force a
single, sharpened decision per project_type; mixing is a
retrieval signal captured in `applicable_conditions`.

## Maintenance

- Adding a value: allowed without ADR if consistent with
  `docs/product/Product.md` Section 2.
- Renaming a value: breaking, requires ADR. (CKOs may
  already cite the old value.)
- Removing a value still in use: breaking, requires ADR.
