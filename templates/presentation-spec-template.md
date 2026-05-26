---
title: "{Presentation Title}"
status: draft            # draft | ready
audience: "{audience}"   # exec | arb | dev | devops | mixed | free-form
scope: "{scope}"         # devops | platform | product | data | security | ml | mixed
length: standard         # short | standard | long
slide_count: 18
theme: default
transition: slide-left
image_style: "clean, modern, technical illustration, isometric, soft palette"
created: {YYYY-MM-DD}
source_type: ad           # ad | repo | branches | session | topic | hybrid
sources:
  ad:
    path: AD.md
  repo: null
  branches: []             # e.g. [{ref: feature/payments, base: main, pr: 412}]
  session: null            # e.g. {path: ~/.claude/projects/.../session.jsonl}
  topic: null              # free-form brief
story_shape: rw-view-ordering   # rw-view-ordering | branches-release | session-recap | repo-tech-tour | topic-talk | hybrid
perspectives:              # only when story_shape includes R&W (ad/hybrid)
  - security
  - availability
  - evolution
view_ordering:             # used when story_shape = rw-view-ordering
  - context
  - drivers
  - functional
  - deployment
  - operational
  - perspectives
  - risks
segments:                  # generic blocks — used by non-R&W story shapes (and hybrid inserts)
  # - id: whats-changing
  #   from_source: branches
  #   slides: 4
  #   inserted_after: functional   # only for hybrid
# ordering rationale: <which reference file drove the choice>, e.g. sources/ad-md/rw-view-selection.md + scopes/devops-platform.md
---

# Presentation Spec — {Title}

This file is the **source of truth** for the deck. `/presentation.implement` renders `slides.md` from this spec — never edit `slides.md` directly.

## Story / Central Message

> *One sentence the audience should remember.*

## Audience

- **Primary**: {who}
- **Secondary**: {who, optional}
- **What they care about**: {one-liner}

## Slides

<!--
Each `### Slide NN` block becomes one Slidev slide.
Fields:
  id            — stable identifier (slug)
  view          — context | functional | information | concurrency | development | deployment | operational | perspectives | meta
  title         — slide title
  key_message   — one-sentence takeaway
  bullets       — 3–5 max
  diagram       — path/anchor to an existing diagram, or `TBD` or `none`
  image_prompt  — natural-language prompt for visual; or `none`
  speaker_notes — 2–3 sentences for the presenter
-->

### Slide 01
- **id**: s01-title
- **view**: meta
- **title**: {Project Name} — Architecture Overview
- **key_message**: Why this architecture, for whom, and what's next.
- **bullets**:
  - Audience: {audience}
  - Scope: {scope}
  - Date / version
- **diagram**: none
- **image_prompt**: A clean isometric illustration of a layered cloud-native platform, soft palette, no text
- **speaker_notes**: Open with the central problem. Set expectations: this deck covers context, key decisions, and risks — in ~20 minutes.

### Slide 02
- **id**: s02-exec-summary
- **view**: meta
- **title**: Executive Summary
- **key_message**: Three things to take away in 60 seconds.
- **bullets**:
  - {takeaway 1}
  - {takeaway 2}
  - {takeaway 3}
- **diagram**: none
- **image_prompt**: none
- **speaker_notes**: TBD

### Slide 03
- **id**: s03-context
- **view**: context
- **title**: System Context
- **key_message**: What we're building and what it touches.
- **bullets**:
  - {external system 1}
  - {external system 2}
  - {trust boundary}
- **diagram**: AD.md#context-diagram
- **image_prompt**: TBD
- **speaker_notes**: TBD

<!-- ... continue for all slides ... -->

## Risks & Open Questions

- {risk 1}
- {open question 1}

## Change Log

<!-- /presentation.clarify and /presentation.implement append entries here -->
- {YYYY-MM-DD} init: spec drafted from {source}
