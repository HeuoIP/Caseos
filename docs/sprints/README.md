# Sprint Records

This folder holds sprint-level records.

## What goes here

- **Sprint task specifications** -- one MD per sprint, written by the
  user and executed by Codex. Naming convention:
  `Sprint_NN_<short-title>.md`.
- **Sprint completion logs** -- append-only records of what changed
  during a sprint, e.g. `theme_extension_log.md`.

## What does NOT go here

- ADRs (use `../architecture/`).
- Architecture reviews (use `../reviews/`).
- General documentation (use `../knowledge/`, `../standards/`, ...).

## Sprint record template

```
# Sprint NN -- <Title>

## Goal

One paragraph: what this sprint achieves.

## Existing Modules

List which existing modules are reused as-is.

## New Architecture / Files

Describe the new structure introduced this sprint.

## Deliverables

- [ ] item 1
- [ ] item 2
- [ ] ...

## Important

Constraints, things to NOT do, etc.
```