---
description: Refine the presentation spec through targeted clarifying questions — covers audience, story, view order, perspectives, image style, AND slide-level content alignment before any rendering happens
handoffs:
  - label: Render Slides
    agent: presentation.implement
    prompt: Render Slidev slides and image prompts from the refined spec
    send: true
scripts:
  sh: .specify/extensions/presentation/scripts/bash/setup-presentation.sh "clarify {ARGS}"
  ps: .specify/extensions/presentation/scripts/powershell/setup-presentation.ps1 "clarify {ARGS}"
---

<!-- Extension: presentation -->
<!-- Config: .specify/extensions/presentation/ -->

See `.specify/extensions/presentation/commands/clarify.md` for full command semantics.
