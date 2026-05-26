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

## User Input

```text
$ARGUMENTS
```

Consider user input before proceeding (if not empty).

**Examples**:

- `"15 slides max, focus on resilience"`
- `"For the architecture review board, emphasize ADR rationale"`
- `"Drop the development view — internal team already knows the code layout"`
- Empty: produce a default proposal driven by detected scope.

### Flags

- `--length short|standard|long` — short (~10 slides), standard (~15–20), long (~25–30). Default: `standard`.
- `--audience exec|arb|dev|devops|mixed` — overrides audience hint from `source.json`.
- `--views CSV` — explicit view ordering, e.g. `context,functional,deployment,operational`. Overrides scope-based defaults.
- `--perspectives CSV` — perspectives to weave in (e.g. `security,availability`).
- `--no-images` — produce a text-only spec; skip image-prompt slots.

## Goal

Produce `presentation/spec.md` — a single source of truth that describes **what** each slide says. `implement` later renders this into Slidev `.md` + image prompts; iteration commands edit the spec, not the output.

## Outline

1. Read `presentation/source.json`
2. Consult `references/` (and Synth vault if present) for ordering recipes
3. Choose view ordering based on scope + audience
4. Draft slide outline (one block per slide)
5. Write `presentation/spec.md` from the template
6. Hand off to `presentation.clarify`

---

## Execution Steps

### Phase 1 — Load Manifest

Read `presentation/source.json`. If missing, abort and tell the user to run `/presentation.init` first.

### Phase 2 — Consult Classified Guidance

Read `source.json.references_to_load` — `init` has already classified which subset applies. Load files in this order (earlier wins on conflict, except Synth vault which always wins):

1. **Source-type folder(s)** — `references/sources/<type>/*.md`
   - `ad-md/` → R&W viewpoint selection, perspectives, AD presentation patterns
   - `repository/` → code-archaeology, tech-stack storytelling
   - `feature-branch/` → release-notes, PR storytelling, demo-day patterns
   - `session/` → conversation summarization, decision-log extraction, working-session recap
   - `topic/` → general talk patterns
   - For hybrid sources, load all listed folders; AD-side guidance owns view ordering, branch-/session-side adds evidence and "what's new" slides

2. **Scope file** — `references/scopes/<dominant-scope>.md` (view recipes per scope)

3. **Audience file** — `references/audiences/<audience>.md` (audience-specific ordering and depth)

4. **Synth vault** (if `source.json.synth_vault.detected == true` AND source includes `ad`):
   - `knowledge/guides/rw-ad-presentation-best-practices.md`
   - `knowledge/guides/rw-view-selection-decision-guide.md`
   - `knowledge/guides/rw-platform-engineering-ad-template.md` (if scope is devops/platform)
   - `knowledge/guides/rw-perspectives-when-to-apply.md`
   - **Vault wins on conflict** — it's the most current authoritative source for R&W content.

**Missing files**: log a `(missing: <path>)` note and fall back to the inline defaults in Phase 3. Never fail on missing references — they're guidance, not gating.

**Different source types ≠ different output formats** — every source still produces a slide outline. What changes is the *shape of the story*:

| Source type | Story shape (from references) |
|---|---|
| `ad` | Architecture review: drivers → views → perspectives → risks |
| `repo` | Tech tour: context → stack → key modules → operational reality |
| `branches` | Release readout: before → what changed → why → impact → next |
| `session` | Working recap: problem → exploration → decisions → outcomes → follow-ups |
| `topic` | Talk: hook → context → core idea → evidence → takeaway |
| `hybrid` | Union — typically AD-shape with a "what's changing now" segment from branches/session |

### Phase 3 — Choose Story / Ordering

The right ordering depends on **both** source type and scope.

**Step A — Pick story shape from source type** (Phase 2 table). For AD-only or AD-led hybrids, the story shape is "R&W view ordering" (the matrix below). For non-AD sources, the shape comes from `sources/<type>/*.md`.

**Step B — When story shape = R&W view ordering**, apply the scope-specific recipe (override via `--views`):

| Scope | Default ordering |
|---|---|
| **devops/platform** | Context → Architectural Drivers → Functional (platform surface + internals) → Deployment → Operational → Concurrency (if event-driven) → Perspectives (Security, Availability, Evolution) → Risks |
| **product/app** | Context → Drivers → Functional → Information → Deployment → Perspectives (Security, Performance, Evolution) → Risks |
| **data** | Context → Drivers → Information (data flow) → Functional → Concurrency → Deployment → Perspectives (Performance, Regulation) → Risks |
| **security** | Context (trust boundaries) → Drivers → Functional (auth/authz flow) → Information → Deployment (segmentation) → Perspectives (Security, Regulation) → Risks |
| **mixed** | Default to dominant scope; surface secondary scope's must-have views in clarify |

**Step C — When story shape comes from `branches`/`session`/`repo`/`topic`**, use the recipe from that source folder. Examples (authoritative recipes live in `references/sources/<type>/`):

| Source | Skeleton |
|---|---|
| `branches` | Title → Before (baseline) → What Changed (per branch/PR) → Why (motivation) → Demo/Evidence → Risks/Rollback → What's Next |
| `session` | Title → Problem We Tackled → How We Explored → Key Decisions → What's Working → Open Questions → Follow-Ups |
| `repo` | Title → Context → Tech Stack → Module Tour → Operational Reality → Strengths/Gaps → Roadmap |
| `topic` | Hook → Why It Matters → Core Idea → Evidence/Examples → Takeaway → Q&A prompt |

**Step D — Hybrid sources** combine shapes. Typical pattern:
- `ad + branches` → AD view ordering, with a "What's Changing Now" segment (3–5 slides from the branches recipe) inserted after Functional or before Risks
- `ad + session` → AD view ordering, with a "Today's Decisions" segment inserted near the end
- `repo + session` → repo Tech Tour shape with session-derived "Recent Decisions" segment

Each block in the chosen ordering maps to 1–3 slides (set by `--length`).

### Phase 4 — Draft Slide Outline

For each slide, decide:

- `id` — stable identifier (e.g. `s07-deployment-topology`)
- `view` — which R&W view this slide belongs to (or `meta` for title/exec summary/closing)
- `title` — slide title
- `key_message` — the one-sentence takeaway
- `bullets` — 3–5 bullets max
- `diagram` — link to existing diagram from AD.md, or `TBD`
- `image_prompt` — placeholder prompt for visual (skip if `--no-images`)
- `speaker_notes` — 2–3 sentences for the presenter

**Slide budget heuristics**:

| Length | Total slides | Per view |
|---|---|---|
| short | ~10 | 1 slide per view, 1 title, 1 closing |
| standard | ~18 | 1–2 slides per view, exec summary, drivers slide, risks slide |
| long | ~28 | 2–3 slides per view, full ADR walk-through, per-perspective slides |

### Phase 5 — Write `presentation/spec.md`

Use `templates/presentation-spec-template.md` as the skeleton. The spec is the **regeneratable source of truth** — every iteration in `implement` reads it and writes the rendered output.

### Phase 6 — Summary + Handoff

Print:

```markdown
## Presentation spec drafted

- **Scope**: devops/platform (from source.json)
- **Audience**: Platform Engineering team
- **Length**: standard (18 slides)
- **View ordering**: context → drivers → functional → deployment → operational → perspectives → risks
- **Perspectives woven in**: Security, Availability, Evolution

**Next step**: `/presentation.clarify` to refine, or `/presentation.implement` to render now.
```

## Key Rules

- **Spec, not slides** — never write Slidev markdown here. That's `implement`'s job.
- **Cite the guidance source** for view ordering decisions inside `spec.md` (e.g. `# ordering rationale: rw-ad-presentation-best-practices.md §"Recommended Presentation Order"`).
- **Respect user overrides** — `--views` and `--audience` flags always win.
- **No fabricated content** — when source data is missing for a slide, write `TBD: <what's needed>` and let `clarify` resolve it.

## Context

{ARGS}
