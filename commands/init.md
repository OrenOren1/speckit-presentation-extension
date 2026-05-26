---
description: Detect presentation source (AD.md, repository, feature branches, Claude session, or free-form topic), detect scope, and scaffold the presentation/ folder
handoffs:
  - label: Build Presentation Spec
    agent: presentation.specify
    prompt: Build the presentation spec from the scaffolded source and detected scope
    send: true
scripts:
  sh: .specify/extensions/presentation/scripts/bash/setup-presentation.sh "init {ARGS}"
  ps: .specify/extensions/presentation/scripts/powershell/setup-presentation.ps1 "init {ARGS}"
---

## User Input

```text
$ARGUMENTS
```

**Examples**:

- `"From AD.md"` — architecture-review deck from the repo's `AD.md`
- `"From repo"` — tech-talk deck built by scanning the whole codebase
- `"From branch feature/payments"` — release-readout deck from a single branch diff
- `"From branches feature/auth,feature/billing vs main"` — multi-branch demo deck
- `"From this session"` — recap deck from the current Claude conversation
- `"Topic: Crossplane vs Terraform for platform teams"` — free-form talk
- `"AD.md + branch feature/migration"` — hybrid (AD + what's changing now)
- Empty: auto-detect (priority: AD.md > repo > topic prompt)

### Flags

- `--source TYPE` — one of `ad`, `repo`, `branches`, `session`, `topic`, `hybrid`, `auto` (default `auto`)
- `--ad PATH` — override AD.md path (default `AD.md`)
- `--branches LIST` — comma-separated git refs (e.g. `feature/x,feature/y`)
- `--base REF` — base ref for branch diffing (default: repo's default branch, e.g. `main`)
- `--session PATH` — explicit Claude session transcript file; otherwise auto-resolved (see Phase 1.4)
- `--topic "..."` — free-form brief
- `--scope devops|platform|product|data|security|ml|auto` (default `auto`)
- `--out PATH` (default `presentation/`)
- `--force` — overwrite an existing `presentation/` folder

## Goal

Discover **what the deck is built from** and **what scope it covers**, then scaffold a working folder + `source.json` manifest. This command produces no slides — it sets up everything `specify` needs to build the spec.

## Outline

1. Resolve source(s) — AD / repo / branches / session / topic / hybrid
2. Per source, run the appropriate **ingestion** (parse AD, scan repo, diff branches, etc.)
3. Detect dominant scope (devops/product/data/security/ml)
4. Infer audience hint
5. Detect Synth vault (optional enrichment)
6. Scaffold `presentation/` folder
7. Write `source.json` manifest
8. Hand off to `/presentation.specify`

---

## Execution Steps

### Phase 1 — Source Resolution

Resolve `--source` (or auto-detect):

```
auto-detect priority:
  1. --source flag if provided
  2. user input parses to a known type ("from repo", "from branch X", "from this session", ...)
  3. AD.md exists at repo root → `ad`
  4. .git/ exists with a non-trivial codebase → `repo`
  5. otherwise → prompt user for a topic → `topic`
```

Multiple sources are allowed (`hybrid`); union them.

#### 1.1 — `ad` (AD.md)

- Read `AD.md` (or `--ad PATH`)
- Parse R&W view headings (`## 6.x`), ADRs referenced, stakeholders, perspectives
- Record into manifest under `sources.ad`

#### 1.2 — `repo` (whole repository)

- Run a lightweight scan (same shape as `architect.init` but read-only and faster):
  - Detect languages, frameworks, databases, container/IaC files
  - List top-level modules / sub-systems
  - Surface README highlights
  - Identify entry points (main, app.py, server.ts, etc.)
- If `architect.init` has already produced ADRs at `.specify/drafts/adr.md`, read those instead of re-scanning
- Record into manifest under `sources.repo`

#### 1.3 — `branches` (feature branch diff)

- Resolve `--base` (default: detected default branch — `main`/`master`/`develop`)
- For each ref in `--branches`:
  - `git log --oneline <base>..<ref>` — commit list
  - `git diff --stat <base>..<ref>` — changed files
  - `git diff <base>..<ref>` summary — high-level change description (LLM-summarize)
  - If `gh` is available, pull associated PR titles + bodies
- Record into manifest under `sources.branches[]`

#### 1.4 — `session` (current Claude session)

Resolving the session transcript:

| Priority | Source |
|---|---|
| 1 | `--session PATH` if provided |
| 2 | The current session's own transcript file (when reachable — typically `~/.claude/projects/<repo-slug>/<session-id>.jsonl`) |
| 3 | Prompt the user to paste a summary or point to a file |

Once resolved:
- Summarize the conversation: topics discussed, decisions made, code/files touched, open questions
- Extract a "what we figured out" timeline
- Record into manifest under `sources.session` (path + summary, not the raw transcript)

#### 1.5 — `topic` (free-form)

- Take `--topic "..."` or prompt the user for a 1–3 sentence brief
- Record into manifest under `sources.topic`

#### 1.6 — `hybrid`

Any combination of the above (e.g., `ad + branches`, `repo + session`). Ingest each independently, then in Phase 3 mark which source contributes which kind of evidence:

| Hybrid case | AD/repo contributes | branches/session contributes |
|---|---|---|
| ad + branches | Stable architecture views | What's changing now / migration story |
| ad + repo | Designed intent | Code-confirmed evidence |
| repo + session | Current state | Decisions made this session |
| ad + session | Designed intent | Today's working session output |

### Phase 2 — Scope Detection

Compute keyword hit-counts across **all ingested sources** (weighted: AD = 1.0, repo = 0.7, branches = 1.2 since recent changes signal current priorities, session = 0.8).

Authoritative keyword lists live in `references/scopes/<scope>.md`. Recognized scopes:

| Scope | Examples |
|---|---|
| **devops/platform** | Kubernetes, ArgoCD, Crossplane, GitOps, operators, CRDs, IDP, Backstage |
| **product/app** | feature, user journey, frontend, mobile, billing, onboarding |
| **data** | pipeline, ETL, warehouse, Spark, Kafka, lake, dbt, Airflow |
| **security** | IAM, zero-trust, threat model, encryption, secrets, mTLS |
| **ml/ai** | model, training, inference, RAG, embeddings, LLM |

Top scope wins; if two are within 20%, mark `mixed`.

### Phase 3 — Audience Hint

Per source type:

| Source | Audience hint |
|---|---|
| `ad` | Look for "Stakeholders" / "Audience" sections in AD.md |
| `repo` | If `architect.init` was run, read its stakeholder findings; else null |
| `branches` | Likely demo-day / sprint review → `dev-team` or `mixed` |
| `session` | Whoever the session was with (often `dev-team` or `solo`) |
| `topic` | null — `clarify` will ask |

### Phase 4 — Optional Synth Vault

If `~/.synth/config/projects.json` exists and resolves to a vault with `knowledge/guides/rw-*.md`, record `synth_vault.path` in the manifest. Downstream commands will read those files in addition to the local `references/`.

### Phase 5 — Scaffold

Create the output directory (default `presentation/`):

```
presentation/
├── source.json          # manifest written by this command
├── spec.md              # placeholder
├── slides.md            # placeholder
├── assets/images/       # empty
└── prompts/             # empty
```

Abort with a clear error if the directory exists and `--force` is not set.

### Phase 5.5 — API Key Setup (image generation)

The extension can run prompts-only without any keys, but if the user wants `--generate` to actually produce images they need at least one LLM provider key and (optionally) ImgBB for hosting.

1. **Check** for any of these keys (in this order):
   - Env: `GEMINI_API_KEY`, `GEMINI_API_KEYS`, `OPENAI_API_KEY`, `IMGBB_API_KEY`
   - Files at repo root: `.googleAI-token`, `.gemini-api-key`, `.imgbb-token`
   - `.env` file at repo root

2. **If no keys found** AND user did not pass `--no-images`:
   - Copy `.env.example` (from the extension) to repo-root `.env` if it doesn't exist
   - Print a short notice:
     ```
     No image-generation keys found. Image generation will be skipped.
     To enable, add at least one of:
       - GEMINI_API_KEY (or GEMINI_API_KEYS, multi-key rotation)
       - OPENAI_API_KEY
     Optional for hosted URLs: IMGBB_API_KEY
     Edit `.env` (gitignored) or export as environment variables.
     ```
   - **Do not block** — the rest of init proceeds normally; generation simply runs in prompts-only mode

3. **Ensure `.env` is gitignored**: if a `.gitignore` exists at repo root, append `.env` to it when missing. If no `.gitignore` exists, create one with `.env`. Same for `.googleAI-token`, `.gemini-api-key`, `.imgbb-token`.

4. **Record** key availability into `source.json.image_pipeline`:
   ```json
   "image_pipeline": {
     "providers_available": ["gemini"],
     "storage_remote": false,
     "mode_default": "prompts-only"
   }
   ```
   Downstream `/presentation.implement --generate` reads this to decide what to attempt.

### Phase 6 — Write `source.json`

```json
{
  "source_type": "hybrid",
  "sources": {
    "ad": {
      "path": "AD.md",
      "views_present": ["context", "functional", "deployment", "operational"],
      "adrs_referenced": ["ADR-001", "ADR-007"],
      "stakeholders": ["Platform Eng", "SRE", "Product"]
    },
    "branches": [
      {
        "ref": "feature/payments",
        "base": "main",
        "commits": 23,
        "files_changed": 47,
        "summary": "Adds Stripe webhook handler and refactors order state machine",
        "pr": {"number": 412, "title": "Payments v2"}
      }
    ],
    "repo": null,
    "session": null,
    "topic": null
  },
  "scope": {
    "dominant": "devops",
    "secondary": "product",
    "evidence": [
      {"source": "ad", "keywords": ["Kubernetes", "ArgoCD"], "hits": 12},
      {"source": "branches", "keywords": ["webhook", "billing"], "hits": 8}
    ]
  },
  "audience_hint": "Platform Engineering + SRE",
  "synth_vault": {
    "detected": true,
    "path": "/Users/.../architecture-patterns"
  },
  "references_to_load": {
    "source_folders": ["sources/ad-md", "sources/feature-branch"],
    "scope_file": "scopes/devops-platform.md",
    "audience_file": "audiences/devops-sre.md"
  },
  "next": "/presentation.specify"
}
```

Note the **`references_to_load`** block — `specify` reads this and loads only the relevant reference subset.

### Phase 7 — Handoff Summary

```markdown
## Presentation initialized

- **Source(s)**: hybrid — `AD.md` + branch `feature/payments`
- **Dominant scope**: devops/platform (secondary: product)
- **Audience hint**: Platform Engineering + SRE
- **Synth vault**: detected at /Users/.../architecture-patterns
- **References to load** (specify will read these):
  - sources/ad-md/ (R&W viewpoints + AD presentation patterns)
  - sources/feature-branch/ (release-readout patterns)
  - scopes/devops-platform.md
  - audiences/devops-sre.md

**Next**: `/presentation.specify` to draft the slide outline.
```

## Key Rules

- **No slides.** This command only discovers and scaffolds.
- **Cite evidence** for scope and audience detection.
- **Honor `--force`.** Don't clobber existing `presentation/` folders silently.
- **Source-agnostic manifest.** `specify` should never need to re-read the original sources — everything it needs is in `source.json` (plus `AD.md` itself if `ad` is in the sources list).
- **References are optional.** If a referenced file is missing, log it and fall back to inline defaults. Never fail on missing references.

## Context

{ARGS}
