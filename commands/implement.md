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

## User Input

```text
$ARGUMENTS
```

**Examples**:

- *(empty)* — render the whole deck from `spec.md`
- `--slide 7 "make this slide focus on resilience, drop the cost bullet"`
- `--image 3 "more abstract, less literal"`
- `--reorder 1,2,4,3,5,6` — apply a new slide order without regenerating content
- `--generate` — auto-produce images for any slide whose prompt changed
- `"add a closing slide on migration plan"` — append a new slide to the deck

### Flags

- `--slide N "<edit instruction>"` — re-render slide N only; updates spec entry + slides.md block
- `--image N "<edit instruction>"` — re-prompt image for slide N; rewrites the prompt file (and image if `--generate`)
- `--reorder N1,N2,...` — apply new slide order; updates spec + slides.md without regenerating content
- `--generate` — call the configured image-gen skill/MCP for any slide whose prompt is new or changed
- `--no-images` — skip image prompts entirely on this render
- `--theme NAME` — override Slidev theme (default from `extension.yml`)
- `--dry-run` — print what would change without writing files

## Goal

`implement` is a **deterministic renderer**. It reads `presentation/spec.md` (the source of truth) and produces:

- `presentation/slides.md` — Slidev markdown
- `presentation/prompts/slide-NN.prompt.md` — one image prompt file per image slide
- `presentation/assets/images/slide-NN.png` — generated images (only when `--generate`)

No "intelligence" lives here — view selection, audience reasoning, and story-building happen in `specify`/`clarify`. This command's contract: **given the same spec, produce the same output**.

## Outline

1. Load `spec.md`; validate `status: ready` (warn if not)
2. Dispatch by mode:
   - **Full render** (no flags): regenerate `slides.md` + all prompts
   - **Single slide** (`--slide N`): update spec slide N, re-render only that block
   - **Single image** (`--image N`): rewrite prompt N, optionally regenerate image
   - **Reorder** (`--reorder`): permute spec, regenerate `slides.md` (content unchanged)
3. If `--generate`, call image generator for any new/changed prompts
4. Write outputs
5. Print diff summary

---

## Execution Steps

### Phase 1 — Load & Validate

```bash
# Required files
presentation/spec.md           # source of truth — must exist
presentation/source.json       # written by /presentation.init
```

If `spec.md` has `status: draft`, warn the user and offer to run `/presentation.clarify` first. With `--force`, proceed anyway.

### Phase 2 — Dispatch by Mode

#### Mode A — Full render (no mode flags)

1. Wipe `presentation/slides.md` (back up to `slides.md.bak` first)
2. Emit Slidev header from `templates/slidev-template.md` using spec frontmatter (title, theme, transition)
3. For each slide in `spec.md`:
   - Render slide block (see "Slide Block Rendering" below)
   - Append to `slides.md`
   - Write/update `prompts/slide-NN.prompt.md`
4. If `--generate`, batch-generate all images

#### Mode B — Single slide (`--slide N "<edit>"`)

1. Locate slide N in `spec.md`
2. Apply the user's edit instruction to that slide's fields (title / key_message / bullets / etc.)
3. Re-render only slide N's block in `slides.md` (preserve surrounding slides byte-for-byte)
4. Update `prompts/slide-NN.prompt.md` if the slide owns an image and the visual context changed

#### Mode C — Single image (`--image N "<edit>"`)

1. Update slide N's `image_prompt` field in `spec.md`
2. Rewrite `prompts/slide-NN.prompt.md`
3. If `--generate`, regenerate `assets/images/slide-NN.png`
4. **Do not touch** `slides.md` content text (images embed via `<img src>` referencing the path)

#### Mode D — Reorder (`--reorder N1,N2,...`)

1. Validate: list must be a permutation of existing slide numbers
2. Reorder slides in `spec.md` (renumber `id` suffixes if used)
3. Regenerate `slides.md` from the new order (content unchanged, just resequenced)
4. Rename prompt files to match new numbering

### Phase 3 — Slide Block Rendering

Each spec slide becomes a Slidev block. Reference: `references/slidev-cheatsheet.md` for syntax. Default template:

```markdown
---
layout: default
transition: slide-left
---

# {title}

{key_message_as_subtitle_or_pullquote}

- {bullet_1}
- {bullet_2}
- {bullet_3}

<!--
Speaker notes:
{speaker_notes}
-->
```

For slides with an image:

```markdown
---
layout: image-right
image: ./assets/images/slide-{NN}.png
---

# {title}
...
```

For slides with a mermaid diagram (pulled from AD.md if `diagram:` points to one):

````markdown
```mermaid
{embedded diagram}
```
````

### Phase 4 — Image Prompt Files

For each image-bearing slide, write `presentation/prompts/slide-NN.prompt.md`:

```markdown
# Slide {NN} — {title}

**Style**: {image_style from spec.md, falling back to extension default}
**Aspect**: 16:9
**Negative**: text, watermarks, logos

**Prompt**:
{image_prompt}

**Context** (for the human or auto-generator):
- Slide key message: {key_message}
- View: {view}
- Audience: {audience}
```

This is what the user copy-pastes into Midjourney/DALL·E/etc. when running in prompts-only mode.

### Phase 5 — Optional Auto-Generation (`--generate`)

If `--generate` is set AND an image-gen capability is available (skill or MCP), call it per changed prompt:

- Input: the rendered `slide-NN.prompt.md`
- Output: `presentation/assets/images/slide-NN.png`
- On failure: leave the prompt file in place, surface the error, do not block the render

If no image-gen capability is available, print a one-line notice and continue without images.

### Phase 6 — Diff Summary

```markdown
## Render complete

- Mode: single-slide (--slide 7)
- Slides updated: 1 (slide 7 — "Deployment Topology")
- Image prompts updated: 1 (slide 7)
- Images generated: 0 (no --generate)
- Output: presentation/slides.md, presentation/prompts/slide-07.prompt.md

Preview locally:
  npx slidev presentation/slides.md
```

## Key Rules

- **Spec is source of truth.** Any user edit applied via `--slide` or `--image` writes to the spec first, then renders. Editing `slides.md` directly is unsupported (will be overwritten).
- **Surgical updates.** `--slide N` and `--image N` must not touch other slides' content. Full-render mode is the only one that wipes `slides.md`.
- **Backup before wiping.** Full render always writes `slides.md.bak`.
- **Image generation is optional.** Prompts-only mode is the default and must always work.
- **Idempotent.** Two consecutive full renders with the same spec produce byte-identical output.
- **No new intelligence.** If the user asks for substantive content changes ("rewrite the story", "change the audience"), redirect them to `/presentation.clarify`.

## Context

{ARGS}
