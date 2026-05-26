---
description: Build the presentation spec — story, audience, view ordering, slide outline — from the scaffolded source and detected scope
handoffs:
  - label: Refine Spec
    agent: presentation.clarify
    prompt: Refine the presentation spec through clarifying questions
    send: true
  - label: Render Slides
    agent: presentation.implement
    prompt: Render Slidev slides and image prompts from the spec
    send: false
scripts:
  sh: .specify/extensions/presentation/scripts/bash/setup-presentation.sh "specify {ARGS}"
  ps: .specify/extensions/presentation/scripts/powershell/setup-presentation.ps1 "specify {ARGS}"
---

<!-- Extension: presentation -->
<!-- Config: .specify/extensions/presentation/ -->

See `.specify/extensions/presentation/commands/specify.md` for full command semantics.
