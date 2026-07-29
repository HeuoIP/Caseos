# 10 Interview Log

> A working log of expert interviews that feed the CaseOS
> expert handbook. This document is a template and a process
> guide; it is not a record of interviews yet conducted.
> When an interview is conducted, the record lives below the
> process section.

## 1. Purpose

Capture expert knowledge in a structured, comparable form so it
can be reviewed, queried, and folded into the handbook. The
interview log is the bridge between human expertise and the
machine-readable knowledge of the engine.

## 2. Scope

**In scope**
- The structure of an expert interview record.
- The process for conducting an interview.
- The relationship between an interview record and the handbook
  sections it informs.

**Out of scope**
- The interviews themselves (those are appended below as they
  happen).
- A generic interview methodology (use any research method the
  interviewer is trained in).

## 3. Core Concepts

An interview has four parts.

1. **Setup** — who, when, where, with what consent.
2. **Lines of inquiry** — the topics the interviewer explores.
3. **Record** — what the expert said, verbatim where possible.
4. **Handbook delta** — which sections of the handbook should
   change, and how.

The interview is a *feed* to the handbook, not a replacement for
it. The handbook is the source of truth; the interview is a
contribution to that source.

## 4. Heuristics

- **One interview, one decision.** A 60-minute interview should
  produce one to three handbook deltas, not a rewrite.
- **Quote the expert.** Paraphrase loses value; verbatim quotes
  survive review.
- **Record the silence, not just the speech.** What an expert
  refuses to say is also data.
- **Cross-check against the existing handbook.** An expert
  statement that contradicts the handbook is either a bug in
  the handbook or a misunderstanding; either way, it is a
  signal worth recording.

## 5. Vocabulary

- **Line of inquiry** — a topic the interviewer explores.
- **Record** — the verbatim or near-verbatim account of the
  conversation.
- **Handbook delta** — the proposed change to the handbook
  that the interview motivates.
- **Counter-example** — a case the expert cites that
  contradicts an existing heuristic or rule.

## 6. Common Pitfalls

- **Confirmation-bias interviewing.** Asking only the questions
  the interviewer already knows the answer to.
- **Source capture failure.** Recording a paraphrase instead of
  a quote, and then being unable to verify.
- **Handbook drift via single source.** Letting one expert's
  strong opinion rewrite a heuristic without a counter-example.
- **Privacy failure.** Recording an expert's name or
  organisation without consent.

## 7. Cross-References

- All other handbook documents (01 through 09) — the interview
  log feeds all of them.
- `knowledge/decision_rules/Space_Decision_Principles.md` —
  expert interviews may surface new principles.
- 05_Negative_Rules.md — counter-examples to a negative rule
  are reviewed carefully.

## 8. Worked Example

**Record template (use one block per interview).**

```markdown
## Interview YYYY-MM-DD

### Setup
- Interviewee: [Name, role, organisation, experience in years]
- Interviewer: [Name]
- Format: [In person / video / written]
- Duration: [minutes]
- Consent: [Yes / No / Specific scope]
- Language: [Original + translation notes if any]

### Lines of inquiry
1. [Topic the interviewer explored]
2. [Topic]
3. [Topic]

### Record (verbatim, with timestamps where available)
- [Quote or near-quote]
- [Quote]
- [Quote]

### Counter-examples to existing handbook rules
- [Rule X]: [counter-example the expert cited]

### Handbook delta
- [Section YYY in document ZZ]: [proposed change]
- [Section YYY in document ZZ]: [proposed change]

### Open questions raised
- [Question for follow-up]
- [Question for follow-up]

### Action items
- [ ] [Person] [Action] by [Date]
- [ ] [Person] [Action] by [Date]
```

### Worked interview (illustrative, not real)

```markdown
## Interview 2026-08-12 (illustrative)

### Setup
- Interviewee: Senior playground designer, 18 years experience.
- Interviewer: CaseOS research lead.
- Format: Video.
- Duration: 75 minutes.
- Consent: Yes, with attribution to handbook v1 only.
- Language: Mandarin, with English glossary.

### Lines of inquiry
1. How do you decide between a Treehouse and an IP_Sculpture as
   the visual anchor of a playground?
2. What is the most common mistake you see in playground briefs?
3. How do you score a site that you have not visited?

### Record
- "I almost never pick IP_Sculpture first. The Treehouse is the
  arrival; the sculpture is the photo. The arrival has to be
  structural."
- "The most common mistake is to ask for a 'magical' playground
  without specifying the budget for maintenance. Magic rots."
- "I score a site I have not visited by asking three things:
  sun path, slope, and the nearest bathroom. If I cannot get
  those three, I refuse to score."

### Counter-examples to existing handbook rules
- Expert Rule 4 ("A space without a place to sit is not a
  public space"): the expert agreed but added that a public
  space without a place to PEE is worse.

### Handbook delta
- 02_Expert_Rules.md, heuristic 4: extend with the bathroom
  criterion.
- 08_Object_Value_Map.md: add a sub-dimension for
  "arrival-ness" so Treehouse scores higher than IP_Sculpture
  on arrival value.

### Open questions raised
- How does the engine score a site it has not visited?
- How is sun path inferred from a photo?
- How is the nearest bathroom recorded in the site's data model?

### Action items
- [ ] Research lead: draft an "arrival value" sub-dimension in
      08_Object_Value_Map.md.
- [ ] Research lead: add a bathroom criterion to 02_Expert_Rules.md.
- [ ] Engineering: confirm whether sun path can be inferred
      from EXIF + time of day.
```

## 9. Open Questions

- [ ] What is the minimum sample of interviews before a new
  handbook section is considered "expert-validated"?
- [ ] How are conflicting expert opinions resolved? By
  authority, by recency, by sample?
- [ ] When an interview contradicts an existing rule, is the
  rule always revised, or only sometimes?
- [ ] How are expert interviews anonymised for the benchmark
  set?

## 10. Maintenance

- Each interview record is dated and versioned.
- Handbook deltas proposed by interviews are tracked until
  they are either accepted into the handbook or rejected with
  a reason.
- The interview log is reviewed quarterly for stale records.
- The template is itself a candidate for evolution; any change
  to the template is versioned and announced.
