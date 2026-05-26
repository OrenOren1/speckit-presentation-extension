---
description: Render the presentation spec into Slidev slides + per-slide image prompts. Supports granular iteration (--slide, --image, --reorder, --generate).
handoffs:
  - label: Refine Spec
    agent: presentation.clarify
    prompt: Adjust the spec and re-render
    send: false
scripts:
  sh: .specify/extensions/presentation/scripts/bash/setup-presentation.sh "implement {ARGS}"
  ps: .specify/extensions/presentation/scripts/powershell/setup-presentation.ps1 "implement {ARGS}"
---

<!-- Extension: presentation -->
<!-- Config: .specify/extensions/presentation/ -->

See `.specify/extensions/presentation/commands/implement.md` for full command semantics.
