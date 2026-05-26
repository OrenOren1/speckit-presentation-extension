---
description: Generate and refine Mermaid diagrams for presentation slides. Audit diagram gaps, synthesize new diagrams from slide content, extract and simplify diagrams from AD.md.
handoffs:
  - label: Render Slides
    agent: presentation.implement
    prompt: Render slides.md from the updated spec (diagrams are now filled in)
    send: false
scripts:
  sh: .specify/extensions/presentation/scripts/bash/setup-presentation.sh "draw {ARGS}"
  ps: .specify/extensions/presentation/scripts/powershell/setup-presentation.ps1 "draw {ARGS}"
---

<!-- Extension: presentation -->
<!-- Config: .specify/extensions/presentation/ -->

See `.specify/extensions/presentation/commands/draw.md` for full command semantics.
