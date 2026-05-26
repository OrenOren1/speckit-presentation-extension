# presentation/references/ — Reference Taxonomy

Knowledge consulted by `/presentation.specify` and `/presentation.clarify`. The directory is **classified by source type** (what the deck is built from) plus cross-cutting categories.

You populate these files manually. The commands cite paths by name — if a file is absent, the command falls back to its own inline defaults.

## Layout

```
references/
├── sources/                       # one folder per source type
│   ├── ad-md/                     # AD.md → Rozanski & Woods framework
│   │   ├── rw-view-selection.md
│   │   ├── rw-perspectives.md
│   │   └── rw-ad-presentation-patterns.md
│   ├── repository/                # whole-codebase scan
│   │   ├── code-archaeology.md
│   │   ├── tech-stack-storytelling.md
│   │   └── dependency-narrative.md
│   ├── feature-branch/            # one or more git refs (diff vs base)
│   │   ├── release-notes-patterns.md
│   │   ├── pr-storytelling.md
│   │   └── demo-day-template.md
│   ├── session/                   # current Claude session transcript
│   │   ├── conversation-summarization.md
│   │   ├── decision-log-extraction.md
│   │   └── working-session-recap.md
│   └── topic/                     # free-form brief
│       └── general-talk-patterns.md
│
├── scopes/                        # CROSS-SOURCE: scope detection + view recipes
│   ├── devops-platform.md
│   ├── product-app.md
│   ├── data.md
│   ├── security.md
│   └── ml-ai.md
│
├── audiences/                     # CROSS-SOURCE: audience-specific strategies
│   ├── exec-cto.md
│   ├── arb-principal.md
│   ├── dev-team.md
│   └── devops-sre.md
│
└── output/                        # rendering knowledge (used by /implement)
    └── slidev-cheatsheet.md
```

## Lookup Rules

`/presentation.specify` loads references in this order, **earliest wins** when guidance conflicts:

1. **Source-type folder** (`sources/<type>/`) — most specific to the input shape
2. **Scope folder** (`scopes/<dominant-scope>.md`) — applies the right view recipes
3. **Audience folder** (`audiences/<audience>.md`) — adjusts ordering and depth
4. **Synth vault** (`knowledge/guides/rw-*.md`) — if detected, overrides matching guidance (authoritative)

For `hybrid` sources (e.g. `ad+repo`), commands load both source-type folders and merge — AD-side guidance owns view ordering, repo-side adds code-confirmed evidence slides.

## What lives where — quick reference

| Concern | File |
|---|---|
| "Which views go in an AD-based deck for an ARB audience?" | `sources/ad-md/rw-view-selection.md` + `audiences/arb-principal.md` |
| "How do I structure a release-readout deck from a branch diff?" | `sources/feature-branch/release-notes-patterns.md` |
| "How do I turn a working session into a 5-slide recap?" | `sources/session/working-session-recap.md` |
| "When is this a devops/platform deck vs. a product deck?" | `scopes/devops-platform.md` / `scopes/product-app.md` |
| "Slidev layout for image-right with mermaid?" | `output/slidev-cheatsheet.md` |

## When Synth is present

If `~/.synth/config/projects.json` resolves to an active vault and `knowledge/guides/rw-*.md` exist, those files are loaded **in addition to** `sources/ad-md/*` and take precedence when guidance conflicts. The local files remain the offline-safe fallback.
