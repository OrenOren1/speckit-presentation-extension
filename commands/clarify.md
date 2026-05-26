---
description: Refine the presentation spec through targeted clarifying questions (audience, story, view order, perspectives, image style)
handoffs:
  - label: Render Slides
    agent: presentation.implement
    prompt: Render Slidev slides and image prompts from the refined spec
    send: true
scripts:
  sh: .specify/extensions/presentation/scripts/bash/setup-presentation.sh "clarify {ARGS}"
  ps: .specify/extensions/presentation/scripts/powershell/setup-presentation.ps1 "clarify {ARGS}"
---

## User Input

```text
$ARGUMENTS
```

**Examples**:

- `"Audience is the CTO + 2 principal engineers"`
- `"Reorder: put deployment before functional"`
- `"Cut slides 12–14"`
- `"Image style: dark mode, neon, cyberpunk"`
- Empty: ask a default round of clarifying questions.

### Flags

- `--max-questions N` (default `5`) — cap on the number of questions asked per round
- `--silent` — skip questions; apply user input directly to the spec

## Goal

Take `presentation/spec.md` from "auto-drafted proposal" to "ready to render" by asking targeted questions and applying the answers.

## Outline

1. Read `presentation/spec.md` and `presentation/source.json`
2. Identify ambiguous or `TBD:` items
3. Ask up to N targeted questions (use `AskUserQuestion` when available)
4. Apply answers to the spec
5. Loop: ask → apply → confirm
6. Mark spec as `status: ready` when no `TBD:` items remain and the user confirms

---

## Execution Steps

### Phase 1 — Diagnose Gaps

Scan `presentation/spec.md` for:

| Gap type | How to spot |
|---|---|
| Audience under-specified | `audience: TBD` or generic ("mixed") |
| Story missing | `key_message:` is empty or generic |
| View ordering rationale missing | No `# ordering rationale:` comment |
| Image style undefined | `image_style: default` or absent |
| Slides with `TBD:` bullets | Search for `TBD:` markers |
| Perspectives unclear | Spec mentions perspective names but no slide owns it |

### Phase 2 — Compose Questions

Pick the **top N gaps** (default 5). Frame each as a multiple-choice question with sensible defaults. Use `AskUserQuestion` if available; otherwise present a numbered list and wait for a free-form reply.

Standard question bank (pick the relevant ones):

1. **Audience precision**
   - Who's in the room? Exec/CTO / ARB / Dev team / DevOps & SRE / Mixed
2. **Story / central message**
   - What's the single sentence the audience should remember?
3. **View ordering preference**
   - Keep the proposed order, or move a view up/down?
4. **Perspectives to highlight**
   - Which 2–3 perspectives matter most? (Security, Performance, Availability, Evolution, Regulation, …)
5. **Image direction**
   - Style: clean/isometric / dark cyberpunk / hand-drawn / photoreal / no images
6. **Length / pacing**
   - Confirm slide count, or trim?
7. **ADR depth**
   - One ADR-walkthrough slide vs. inline ADR mentions inside each view's slides?
8. **Risks/closing**
   - Include explicit "Risks & Open Questions" slide, or fold into perspectives?

### Phase 3 — Apply Answers

For each answer, **edit `presentation/spec.md`** in place. Be surgical — don't rewrite slides the user didn't touch. Record the change in a `## Change Log` section at the bottom of the spec:

```markdown
## Change Log
- 2026-05-26 clarify: audience set to "ARB (CTO + 2 principal engineers)"
- 2026-05-26 clarify: reordered — deployment moved before functional per user
```

### Phase 4 — Loop or Exit

If new gaps are introduced by the answers (e.g., "we added a regulation perspective — need a slide for it"), ask one more focused round. Otherwise:

- Set `status: ready` in the spec's frontmatter
- Print a diff summary of what changed
- Suggest the next step

### Phase 5 — Summary + Handoff

```markdown
## Spec refined and ready

- 5 questions asked, 5 answers applied
- 3 slides updated, 1 slide added (Regulation perspective)
- View ordering: unchanged
- Status: **ready**

**Next step**: `/presentation.implement` to render slides + image prompts.
```

## Key Rules

- **Ask, don't assume** — but cap at `--max-questions` per round to avoid fatigue.
- **Show defaults** — every question should have a recommended option so users can `Enter`-through.
- **Edit surgically** — preserve user-authored sections of the spec.
- **Change log is mandatory** — every clarify pass appends entries.
- **Idempotent** — re-running clarify on a `status: ready` spec should ask "anything to refine?" and exit cleanly if not.

## Context

{ARGS}
