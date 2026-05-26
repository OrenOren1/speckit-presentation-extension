# Synth Integration — Optional Knowledge Enrichment

The presentation extension is **self-contained**: it ships with offline references under `references/sources/`, `references/scopes/`, etc., and works without any external dependencies.

When a [Synth](https://github.com/orensito/synth) vault is also installed and points to an `architecture-patterns`-shaped knowledge base, the extension uses it as **authoritative enrichment** — the vault wins on conflict.

## How the extension detects Synth

`/presentation.init` and `/presentation.specify` both check for:

```
~/.synth/config/projects.json
```

If present, they resolve the `active_project` to a vault path and verify it contains `knowledge/HOW-TO-QUERY.md`. If both conditions hold, `source.json.synth_vault.detected = true` and downstream commands consult the vault.

## The synth skill

The actual fetching is delegated to the **`synth` Claude Code skill** (lives at `~/.claude/skills/synth/SKILL.md`). The skill encapsulates:

- Vault detection and path resolution
- The two access modes (direct file reads vs Synth chat API)
- The taxonomy contract (`for-ad` / `for-presentation` / `shared`)
- Per-consumer recipes for what to read

When this extension's commands need vault knowledge, the recommended pattern is:

```
1. /presentation.specify detects synth_vault.detected = true in source.json
2. The command invokes (or implies) the synth skill with a task description,
   e.g. "Read for-presentation guidance for an ARB-audience platform deck"
3. The skill returns paths + extracted guidance
4. The command uses that guidance to drive view ordering, perspectives, etc.
```

## Vault schema (consumer-side)

The vault is expected to follow the schema documented in its `knowledge/HOW-TO-QUERY.md`. The contract this extension relies on:

| Path | Purpose |
|---|---|
| `knowledge/HOW-TO-QUERY.md` | The schema + per-consumer recipes (read first) |
| `knowledge/taxonomy.md` | File-level classification (`for-ad` / `for-presentation` / `shared`) |
| `knowledge/guides/rw-ad-presentation-best-practices.md` | `for-presentation` — view ordering, audience strategies |
| `knowledge/guides/rw-view-selection-decision-guide.md` | `shared` — stakeholder ↔ view matrix |
| `knowledge/presentation/*.md` | `for-presentation` — slide treatment patterns |

If any of these paths are missing from a future vault, the extension falls back to its bundled references silently.

## What this extension reads from the vault

Filter: `for-presentation` + `shared` (never `for-ad`-only files, unless the source is AD-based — then `for-ad` is also relevant for understanding which views are present).

Specific recipes are in the vault's `HOW-TO-QUERY.md` under "Per-consumer recipes — presentation extension".

## Fallback behavior

When the vault is absent:

- `references/sources/ad-md/` provides condensed R&W view-selection + presentation guidance
- `references/scopes/*` provides scope-specific view recipes
- `references/audiences/*` provides audience strategies
- `references/output/slidev-cheatsheet.md` provides renderer-specific tips

These are intentionally a **thin subset** of the vault — vault users get richer guidance, but no one is blocked without it.
