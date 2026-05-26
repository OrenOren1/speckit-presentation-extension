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

**Content / structure:**
- `--slide N "<edit instruction>"` — re-render slide N only; updates spec entry + slides.md block
- `--reorder N1,N2,...` — apply new slide order; updates spec + slides.md without regenerating content
- `--no-images` — skip image prompts entirely on this render
- `--theme NAME` — override Slidev theme (default from `extension.yml`)
- `--dry-run` — print what would change without writing files

**Image pipeline (per-slide granular controls):**
- `--image N "<edit instruction>"` — modify the prompt text for slide N (writes spec; does NOT call image gen)
- `--regenerate-prompt N` — re-synthesize the prompt for slide N from its current content (title + key_message + bullets + diagram)
- `--mermaid-to-prompt N` — read the mermaid block on slide N and convert it to a natural-language image prompt (illustrated visual that captures the same flow/relationships)
- `--generate [N|all]` — actually call the image generator. Provider chain: Gemini → OpenAI. Uploads to ImgBB if `IMGBB_API_KEY` is set.
- `--regenerate-image N` — alias for `--generate N`; useful after `--image` or `--regenerate-prompt`
- `--provider gemini|openai` — force a specific provider (overrides chain)
- `--model NAME` — force a specific model
- `--style "..."` — override `image_style` for this render
- `--cover-from N` — promote slide N's image to be the deck cover

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

### Phase 4.1 — Prompt Synthesis & Modification

Three ways a prompt can be (re)created — all of them write to `spec.md` first, then re-emit `prompts/slide-NN.prompt.md`:

**1. `--image N "<edit instruction>"`** — *modify*
- Apply the natural-language edit to slide N's existing `image_prompt` field (e.g. "more abstract, drop the cloud icon")
- Surgical: don't touch other slides

**2. `--regenerate-prompt N`** — *regenerate from slide content*
- Recompose `image_prompt` from the current slide fields: `title`, `key_message`, `bullets`, `view`, plus `image_style`
- Useful after the slide's content changed via `--slide N` and you want the visual to match
- Template:
  > `<image_style>. Depicting <key_message>. Visual elements suggest: <bullets[0..2] reframed as objects/scenes>. <16:9, no text labels.>`

**3. `--mermaid-to-prompt N`** — *mermaid → illustrated prompt* (NEW capability)

When a slide owns a mermaid block (because `diagram:` in the spec points to a `mermaid` fence in `AD.md` or an inline diagram), this flag converts the diagram **semantics** to a natural-language image prompt — useful when an architecture review deck wants a polished illustration rather than a raw mermaid render.

Process:
1. Locate the mermaid block referenced by slide N's `diagram:` field
2. Parse the diagram type (`graph LR`, `sequenceDiagram`, `flowchart TD`, `C4Context`, etc.)
3. Extract nodes (with labels) and edges (with labels)
4. Synthesize a prompt using this skeleton:

   ```
   {style_hint from extension.yml mermaid_to_prompt}.
   Depicting {N} components: {node_labels}.
   Their relationships: {edge_descriptions written as natural language flow}.
   Layout: {match diagram orientation — LR → left-to-right, TD → top-down}.
   16:9, minimal text labels, focus on visual hierarchy.
   ```

5. Write the synthesized prompt to slide N's `image_prompt`; preserve the original mermaid (don't delete — it's still useful as a fallback)

**Diagram type → prompt hint** quick reference:

| Mermaid type | Visual treatment |
|---|---|
| `graph LR` / `flowchart LR` | Horizontal flow, left-to-right arrows, pipeline aesthetic |
| `graph TD` / `flowchart TD` | Top-down hierarchy, tree or layered cake |
| `sequenceDiagram` | Time-ordered interaction; choreography or relay-race metaphor |
| `C4Context` / `C4Container` | Layered system map; concentric or layered cake |
| `stateDiagram-v2` | State machine; circuits, gears, or transformation chain |
| `erDiagram` | Data model; connected entities, blueprint style |

### Phase 5 — Image Generation (`--generate`)

Generates actual images by calling provider APIs. This is the **only** phase that hits external services.

#### 5.1 Key resolution

Resolved in this order; first hit wins:

1. Environment variables: `GEMINI_API_KEY` → `GEMINI_API_KEYS` (comma- or newline-separated) → `OPENAI_API_KEY`
2. Repo-root files: `.googleAI-token`, `.gemini-api-key` (one key per line, rotate on 429/401/403)
3. `.env` file in repo root (loaded if present; **never committed** — `.env` is auto-added to `.gitignore` by `/presentation.init`)

If no provider key is found, abort the generation step with a clear message and continue rendering without images.

#### 5.2 Provider chain

```
1. Try Gemini (Nano Banana / Nano Banana Pro):
     - model: gemini-2.5-flash-image (default)
     - on quota/auth errors (429/401/403), rotate to next key in GEMINI_API_KEYS
     - on persistent failure, fall through to OpenAI
2. Try OpenAI DALL-E 3:
     - model: dall-e-3
     - 1024x1024 (square) or 1792x1024 (16:9)
3. If both fail: surface error, leave previous image (if any) in place, mark prompt file with a `# generation_failed:` note
```

Force a specific provider with `--provider gemini|openai` and a specific model with `--model NAME`.

#### 5.3 Generation per slide

For each slide N being generated:

1. Read prompt from `prompts/slide-NN.prompt.md` (or spec field if file missing)
2. Call provider; receive image bytes
3. Save locally: `presentation/assets/images/slide-NN.png`
4. **If `IMGBB_API_KEY` is set (env or `.imgbb-token` file)**:
   - Upload to ImgBB; receive `i.ibb.co` URL
   - In `slides.md`, replace the image reference with the remote URL
   - **Archive the original prompt** as a one-line HTML comment immediately above the image, matching the blog-post convention:
     ```markdown
     <!-- image_prompt:archive index=07 b64=<base64url> -->
     ![Deployment topology illustration](https://i.ibb.co/.../slide-07.png)
     ```
   - This way the prompt is never lost even if the prompt file is later deleted
5. If `IMGBB_API_KEY` is absent: keep local relative paths in `slides.md` (`./assets/images/slide-NN.png`); still write the archive comment so the prompt is preserved

#### 5.4 Helper script

The actual provider calls and ImgBB upload live in `scripts/generate_images.py`. The command invokes it as:

```bash
python .specify/extensions/presentation/scripts/generate_images.py \
  --spec presentation/spec.md \
  --slides {N|all} \
  [--provider gemini|openai] [--model NAME]
```

The script reads the same `extension.yml` defaults and produces a JSON report on stdout listing which slides succeeded/failed and where images were stored.

### Phase 5.5 — Cover Handling (`--cover-from N`)

If the user wants slide N's image to also serve as the deck cover:

1. Copy the slide-N image to `assets/images/cover.png` (and upload to ImgBB if enabled)
2. Update spec frontmatter: `image: <cover URL or path>`
3. Re-render slide 01 (the title slide) to reference the cover

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
