---
description: Detect presentation source (AD.md or free-form topic), detect scope, and scaffold the presentation/ folder
handoffs:
  - label: Build Presentation Spec
    agent: presentation.specify
    prompt: Build the presentation spec from the scaffolded source and detected scope
    send: true
scripts:
  sh: .specify/extensions/presentation/scripts/bash/setup-presentation.sh "init {ARGS}"
  ps: .specify/extensions/presentation/scripts/powershell/setup-presentation.ps1 "init {ARGS}"
---

<!-- Extension: presentation -->
<!-- Config: .specify/extensions/presentation/ -->
<!-- This agent file mirrors commands/init.md — see that file for the full instructions. -->

See `.specify/extensions/presentation/commands/init.md` for full command semantics.
