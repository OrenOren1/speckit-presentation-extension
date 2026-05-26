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
/presentation.implement                            # full re-render from spec.md
/presentation.implement --slide 7 "..."            # edit + re-render one slide
/presentation.implement --image 3 "..."            # re-prompt + re-render one image
/presentation.implement --reorder 1,2,4,3,5,6      # permute order without regenerating content
/presentation.implement --generate                 # auto-produce images for changed prompts
/presentation.implement --no-images                # text-only render
```

All edits flow through `spec.md` (the source of truth), then render. Direct edits to `slides.md` are unsupported — they'll be overwritten on the next render. `slides.md.bak` is always written before a full render.

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
├── extension.yml              # speckit extension manifest
├── commands/
│   ├── init.md                # source/scope/audience detection
│   ├── specify.md             # spec builder
│   ├── clarify.md             # Q&A refinement
│   └── implement.md           # Slidev renderer
├── agents/
│   └── presentation.{init,specify,clarify,implement}.agent.md
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

- [ ] Populate `references/sources/ad-md/` with condensed R&W guidance
- [ ] Populate `references/sources/feature-branch/` with release-readout patterns
- [ ] Populate `references/sources/session/` with summarization patterns
- [ ] Populate `references/scopes/` and `references/audiences/`
- [ ] `references/output/slidev-cheatsheet.md`
- [ ] Bash setup script (`scripts/bash/setup-presentation.sh`) for path resolution + flag parsing, matching `architect/`'s pattern
- [ ] Smoke-test on a real AD-based deck
- [ ] Smoke-test on a `branches` source
- [ ] Smoke-test on a `session` source
- [ ] Open PR against `tikalk/agentic-sdlc-spec-kit`

---

## License

MIT (matching the parent `agentic-sdlc-spec-kit` license, pending merge).
