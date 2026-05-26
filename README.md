# speckit-presentation-extension

> **Status: DRAFT** — exploration for a future PR to [`tikalk/agentic-sdlc-spec-kit`](https://github.com/tikalk/agentic-sdlc-spec-kit).

A speckit extension that generates and iterates on **Slidev presentations** from architecture descriptions, codebases, feature branches, Claude sessions, or free-form topics — using the same `init → specify → clarify → implement` methodology as the [`architect`](https://github.com/tikalk/agentic-sdlc-spec-kit/tree/main/extensions/architect) extension.

---

## Why this exists

Architects, platform engineers, and dev teams routinely need to turn what they've already written down — an `AD.md`, a feature branch, a working session — into a presentation. Today that means manually re-shaping content for the audience, picking the right view order, and writing image prompts from scratch.

This extension treats the **presentation as a regeneratable artifact**: a single `spec.md` is the source of truth; slides and image prompts are rendered deterministically from it; single-slide or single-image regeneration is cheap.

When the source is an `AD.md`, it applies the **Rozanski & Woods Viewpoints & Perspectives** framework to pick the right view ordering for the detected scope (devops/platform/product/data/security/ml) and audience (exec/ARB/dev/SRE).

---

## Methodology — mirrors `architect/`

| Phase | Command | Output |
|---|---|---|
| **Discover** | `/presentation.init` | Detect source(s) + scope + audience; scaffold `presentation/` folder; write `source.json` manifest |
| **Spec** | `/presentation.specify` | Build the slide outline (`spec.md`) using classified references |
| **Refine** | `/presentation.clarify` | Ask targeted questions; apply answers surgically; mark spec `ready` |
| **Draw** *(optional)* | `/presentation.draw` | Audit diagram gaps; synthesize Mermaid diagrams per slide; author/generate AI images with model selection + ImgBB upload |
| **Render** | `/presentation.implement` | Deterministically render Slidev `slides.md` + per-slide image prompts |

The "intelligence" — scope detection, view selection, story shaping — lives in `init` + `specify`. `implement` is a dumb renderer: same spec → same output, byte-for-byte. That's what makes single-slide and single-image regeneration cheap.

---

## Source types

`/presentation.init` accepts any of these, or a combination (`hybrid`):

| Source | Ingests | Story shape |
|---|---|---|
| `ad` | `AD.md` | R&W viewpoint ordering (drivers → views → perspectives → risks) |
| `repo` | Whole codebase (languages, frameworks, modules) | Tech tour (context → stack → modules → ops) |
| `branches` | One or more git refs (diff vs base, PR titles via `gh`) | Release readout (before → what changed → why → impact → next) |
| `session` | Current Claude session transcript | Working recap (problem → exploration → decisions → outcomes) |
| `topic` | Free-form brief | Talk (hook → context → core idea → evidence → takeaway) |
| `hybrid` | Any combination, e.g. `ad+branches` | AD ordering with a "what's changing" segment inserted |

---

## Synth — external knowledge base (optional)

This extension is **self-contained** but can be enriched by [Synth](https://github.com/orensito/synth), a local FastAPI service that maintains a curated knowledge vault. When a vault is detected at `~/.synth/config/projects.json`, commands consult it as the authoritative source for R&W methodology, AD-presentation patterns, and architecture examples — the vault wins on conflict with bundled references.

Both this extension and the [`architect`](https://github.com/tikalk/agentic-sdlc-spec-kit/tree/main/extensions/architect) extension delegate vault access to the **`synth` Claude Code skill** (`~/.claude/skills/synth/SKILL.md`). The skill encapsulates detection, two access modes (direct file reads or chat API), and the **taxonomy contract** that classifies each vault file as `for-ad`, `for-presentation`, or `shared`.

See [`references/synth-integration.md`](references/synth-integration.md) for the full integration design.

The vault's `knowledge/HOW-TO-QUERY.md` documents the schema and per-consumer recipes — the presentation extension reads `for-presentation` + `shared` (and `for-ad` when the source is AD-based).

---

## Classified references

References are organized by **what kind of source the deck is built from**, not as a flat list. Commands load only the relevant subset (declared in `source.json.references_to_load`).

```
references/
├── sources/
│   ├── ad-md/           # R&W viewpoints + perspectives + AD presentation patterns
│   ├── repository/      # code-archaeology, tech-stack storytelling
│   ├── feature-branch/  # release-notes, PR storytelling, demo-day templates
│   ├── session/         # conversation summarization, decision-log extraction
│   └── topic/           # general talk patterns
├── scopes/              # CROSS-SOURCE: devops/product/data/security/ml view recipes
├── audiences/           # CROSS-SOURCE: exec/ARB/dev/SRE strategies
└── output/              # slidev syntax tips for the renderer
```

**Reference loading rules** (earliest wins on conflict, except Synth vault which always wins):

1. Source-type folder(s) — `sources/<type>/*.md`
2. Scope file — `scopes/<dominant-scope>.md`
3. Audience file — `audiences/<audience>.md`
4. (Optional) Synth vault — `knowledge/guides/rw-*.md` if detected at `~/.synth/config/projects.json`

Missing files log a notice and fall back to inline command defaults — references are guidance, not gating.

---

## Iteration — granular regeneration

`implement` supports surgical updates so you never have to regenerate the whole deck to fix one slide:

```bash
# Content / structure
/presentation.implement                            # full re-render from spec.md
/presentation.implement --slide 7 "..."            # edit + re-render one slide
/presentation.implement --reorder 1,2,4,3,5,6      # permute order, content unchanged

# Image pipeline (per slide, all routed through spec.md)
/presentation.implement --image 3 "more abstract"  # modify prompt text only
/presentation.implement --regenerate-prompt 7      # rebuild prompt from slide content
/presentation.implement --mermaid-to-prompt 4      # convert slide-4 mermaid → image prompt
/presentation.implement --generate 7               # actually call the provider for slide 7
/presentation.implement --generate all             # generate every slide that needs it
/presentation.implement --regenerate-image 7       # alias for --generate 7
/presentation.implement --provider openai          # force a specific provider
/presentation.implement --cover-from 5             # promote slide 5's image to the deck cover
/presentation.implement --no-images                # text-only render
```

All edits flow through `spec.md` (the source of truth), then render. Direct edits to `slides.md` are unsupported — they'll be overwritten on the next render. `slides.md.bak` is always written before a full render.

---

## Image pipeline

The extension ships with a real image-generation pipeline (mirrors the conventions of the [`blog-post`](https://github.com/) skill so keys and file patterns are portable across both toolchains).

### Capabilities

| Capability | Flag | What it does |
|---|---|---|
| **Mermaid → prompt** | `--mermaid-to-prompt N` | Reads a slide's mermaid diagram, synthesizes an illustrated-image prompt that captures the same flow/relationships (useful when an architecture review deck wants a polished visual rather than a raw mermaid render) |
| **Regenerate prompt** | `--regenerate-prompt N` | Rebuilds the prompt from the slide's current `title` + `key_message` + `bullets` + `image_style` |
| **Modify prompt** | `--image N "..."` | Applies a natural-language edit to the existing prompt; surgical — doesn't touch other slides |
| **Implement / generate** | `--generate [N\|all]` | Actually calls the provider API, saves the PNG, optionally uploads to ImgBB |

### Providers — Gemini → OpenAI fallback

Provider chain (first usable key wins; force with `--provider`):

1. **Gemini** (Nano Banana / Nano Banana Pro) — `gemini-2.5-flash-image`, `gemini-2.5-pro-image`
   - Multi-key rotation: on 429/401/403 the script automatically retries with the next key from `GEMINI_API_KEYS`, `.googleAI-token`, or `.gemini-api-key` (one key per line)
2. **OpenAI DALL-E 3** — fallback when no Gemini key is usable

### Storage — local by default, ImgBB if key present

- **Always** writes `presentation/assets/images/slide-NN.png` locally
- **If `IMGBB_API_KEY` is set**, also uploads to ImgBB and uses `i.ibb.co` URLs in `slides.md`
- The original prompt is preserved as a base64-encoded HTML comment archived **inline above each image** — even if the prompt file is deleted, the prompt can be recovered:
  ```markdown
  <!-- image_prompt:archive index=07 b64=SXNvbWV0cmlj... -->
  ![Deployment topology](https://i.ibb.co/abc/slide-07.png)
  ```

### API keys — user-provided

`/presentation.init` checks for keys and prints setup instructions if none are found. It also auto-adds `.env` and the key files to `.gitignore`.

Keys are read in this order:

1. Environment variables
2. Repo-root files (one key per line, supports rotation)
3. `.env` file in repo root (gitignored)

| Key | Required for | Where |
|---|---|---|
| `GEMINI_API_KEY` | Gemini image gen | env or `.env` |
| `GEMINI_API_KEYS` | Gemini multi-key rotation | env (comma/newline-separated) |
| `.googleAI-token` / `.gemini-api-key` | Gemini multi-key rotation | repo-root files |
| `OPENAI_API_KEY` | OpenAI DALL-E fallback | env or `.env` |
| `IMGBB_API_KEY` | Hosted image URLs (optional) | env or `.env` |
| `.imgbb-token` | ImgBB single-key form | repo-root file |

Copy `.env.example` to `.env` and fill in what you have. Image generation is fully optional — if no keys are present, the extension stays in prompts-only mode and you can paste the prompt files into Midjourney/DALL·E/etc. manually.

### Helper script

`scripts/generate_images.py` is the actual generator (callable independently for testing):

```bash
python scripts/generate_images.py --spec presentation/spec.md --slides all
python scripts/generate_images.py --spec presentation/spec.md --slides 3,7
python scripts/generate_images.py --spec presentation/spec.md --slides 7 \
  --provider openai --model dall-e-3
```

Outputs a JSON report listing which slides succeeded/failed and where each image was stored (local path and ImgBB URL when applicable).

Dependencies (install only when using `--generate`):

```bash
pip install google-genai openai pyyaml
```

---

## Output layout

After a full workflow:

```
presentation/
├── source.json          # init: source + scope + audience manifest
├── spec.md              # specify + clarify: source of truth
├── slides.md            # implement: Slidev markdown
├── slides.md.bak        # implement: backup before full render
├── assets/
│   └── images/          # implement (--generate): generated images
└── prompts/
    └── slide-NN.prompt.md   # implement: per-slide image prompts (always written)
```

Preview locally with:

```bash
npx slidev presentation/slides.md
```

---

## Repository layout

```
.
├── extension.yml              # speckit extension manifest (incl. image pipeline config)
├── .env.example               # template — copy to .env (gitignored)
├── commands/
│   ├── init.md                # source/scope/audience detection + key setup
│   ├── specify.md             # spec builder
│   ├── clarify.md             # Q&A refinement
│   ├── draw.md                # Mermaid diagram generation + image prompt authoring + interactive AI image gen
│   └── implement.md           # Slidev renderer + image pipeline (mermaid→prompt, generate, ImgBB)
├── agents/
│   └── presentation.{init,specify,clarify,draw,implement}.agent.md
├── scripts/
│   └── generate_images.py     # provider chain (Gemini → OpenAI), ImgBB upload, key rotation
├── templates/
│   ├── presentation-spec-template.md
│   └── slidev-template.md
└── references/                # (empty subdirs — populate manually)
    ├── README.md              # taxonomy + lookup rules
    ├── sources/{ad-md,repository,feature-branch,session,topic}/
    ├── scopes/
    ├── audiences/
    └── output/
```

---

## Installation (after merge into `agentic-sdlc-spec-kit`)

Once this lands in spec-kit, install it into any speckit-enabled repo via the standard extension installer (same flow as `architect/`).

For now, to try it locally:

```bash
# Copy the extension into a target repo
cp -r commands templates references extension.yml \
  <target-repo>/.specify/extensions/presentation/
cp agents/*.agent.md <target-repo>/.github/agents/
```

Then in Claude Code inside that repo:

```
/presentation.init "From AD.md"
/presentation.specify --audience arb
/presentation.clarify
/presentation.draw --from-ad        # optional: extract + assign diagrams from AD.md
/presentation.draw --all            # optional: generate missing Mermaid diagrams
/presentation.draw --generate 7     # optional: interactive AI image for slide 7
/presentation.implement --generate
```

---

## Rozanski & Woods alignment (AD source only)

When the source is `ad` (or a hybrid containing `ad`), the extension follows the R&W "Software Systems Architecture" methodology:

- **Views are interrelated** — Functional is the cornerstone; the rest follow
- **Perspectives are cross-cutting quality lenses** — Security, Performance, Availability, Evolution, Internationalization, Location, Regulation, Development Resource
- **Audience-driven ordering** — exec/board decks differ from dev/SRE decks in depth and which views they emphasize

The view ordering matrix per scope (see `commands/specify.md` Phase 3) implements the recommended sequencing from R&W's presentation guidance.

---

## Roadmap

- [x] Image pipeline: provider chain (Gemini → OpenAI), ImgBB upload, key rotation, mermaid→prompt
- [x] `presentation.draw` — Mermaid generation, image prompt authoring (`--prompt`), interactive AI image generation (`--generate`) with model selection + in-session preview + ImgBB upload
- [ ] Populate `references/sources/ad-md/` with condensed R&W guidance
- [ ] Populate `references/sources/feature-branch/` with release-readout patterns
- [ ] Populate `references/sources/session/` with summarization patterns
- [ ] Populate `references/scopes/` and `references/audiences/`
- [ ] `references/output/slidev-cheatsheet.md`
- [ ] Bash setup script (`scripts/bash/setup-presentation.sh`) for path resolution + flag parsing, matching `architect/`'s pattern
- [ ] Smoke-test image generation end-to-end (Gemini path)
- [ ] Smoke-test image generation end-to-end (OpenAI path)
- [ ] Smoke-test ImgBB upload + archive-comment placement in `slides.md`
- [ ] Smoke-test on a real AD-based deck
- [ ] Smoke-test on a `branches` source
- [ ] Smoke-test on a `session` source
- [ ] Open PR against `tikalk/agentic-sdlc-spec-kit`

---

## License

MIT (matching the parent `agentic-sdlc-spec-kit` license, pending merge).
