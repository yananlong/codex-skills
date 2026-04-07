---
name: research-zotero
description: Sync, inspect, and export Zotero user or group libraries for literature-heavy research workflows. Use when Codex needs to reuse a Zotero library or collection as a curated paper corpus, export BibTeX or CSL-JSON, inspect collections/tags/groups, prepare citation artifacts for paper planning, or seed literature review and novelty review from an existing Zotero library. Default to the current user's library when an API key is available and no explicit library is provided.
---

# Research Zotero

## Quick start

1. Use `scripts/inspect_zotero_account.py` first when you need to confirm which library the current API key can see.
2. If no library is specified, default to the current user's library resolved from the provided API key or `$ZOTERO_API_KEY`.
3. Use `scripts/fetch_zotero_items.py` to sync a library, collection, or tag/query slice into normalized JSON.
4. Use `scripts/export_zotero_items.py` when a downstream skill needs BibTeX, CSL-JSON, RIS, or raw exported item payloads.
5. In orchestrated mode, prefer `./zotero/` as the canonical stage root and record actual paths in `artifact-index.md`.

## Modes

### Inspect mode

- Use this when the user wants to know what the current API key can access.
- Resolve the default user library through `/keys/current`.
- Inspect accessible groups when group libraries might matter.

### Sync mode

- Use this when another research skill needs a curated Zotero corpus as structured JSON.
- Sync a whole library or narrow to:
  - collection
  - tags
  - query
  - item type
- Write normalized artifacts that downstream skills can consume without calling Zotero again.

### Export mode

- Use this when another skill or external tool needs citation exports rather than raw Zotero item JSON.
- Export:
  - `bibtex`
  - `csljson`
  - `ris`
  - raw `json`

## Input contract

- Minimum:
  - Zotero API access via `--api-key` or `$ZOTERO_API_KEY`, or Zotero MCP access when available
- Optional:
  - `library_type`: `user` or `group`
  - `library_id`
  - `collection_key`
  - `tags`
  - `query`
  - `item_type`
  - export format
  - output directory or file paths

## Default-library rule

- If no explicit `user` or `group` library is provided and an API key is available, resolve the current key via `/keys/current` and use that user library by default.
- Do not ask the user for a library ID if the API key already resolves it.
- If the key lacks the necessary library access, stop and report the permission gap explicitly.

## Output contract

- Canonical orchestrated directory: `./zotero/`
- Primary sync artifacts:
  - `zotero-account.json`
  - `zotero-items.json`
  - `zotero-sync.md`
- Optional support artifacts:
  - `zotero-groups.json`
  - `library-export.bib`
  - `library-export.csl.json`
  - `library-export.ris`
- `zotero-items.json` should preserve:
  - library type and ID
  - collection key if used
  - tags/query/item type filters
  - item count
  - original Zotero item payloads
- Record output paths in `artifact-index.md` when used inside an orchestrated pack.

## Workflow

### 1) Resolve access first

- Use `scripts/inspect_zotero_account.py`.
- Confirm:
  - default user library
  - accessible groups
  - whether the key can read the relevant library

### 2) Choose the narrowest useful library scope

- Default to the current user's library when the task is broad and no narrower source is specified.
- Prefer a collection, tags, or query when:
  - the full library is too broad
  - the task is for one domain or project
  - a downstream skill needs a focused corpus

### 3) Sync normalized item JSON

- Use `scripts/fetch_zotero_items.py`.
- If no library is specified, let the script resolve the default user library from the key.
- Preserve the raw Zotero item payloads rather than flattening away useful metadata too early.
- When helpful, write `zotero-sync.md` alongside the JSON output.

### 4) Export citation formats only when needed

- Use `scripts/export_zotero_items.py` when the task specifically needs:
  - BibTeX for LaTeX
  - CSL-JSON for citation tooling
  - RIS for external import
- Avoid exporting citation formats as the only artifact if downstream research skills still need full item metadata.

### 5) Hand off to sibling skills

- `research-systematic-literature-review`:
  - consume `zotero-items.json` as a curated discovery/citation-validation source
- `research-novelty-review`:
  - use Zotero collections or tags to seed strongest-overlap searches
- `research-paper-plan`:
  - use exported BibTeX or CSL-JSON plus item metadata for citation planning
- `research-rebuttal`:
  - use the synced library to pull cited sources or related prior art quickly

## References

- `references/zotero-integration.md`
- `references/zotero-artifact-contract.md`

## Scripts

- `scripts/inspect_zotero_account.py`: resolve the default library and accessible groups for the current API key
- `scripts/fetch_zotero_items.py`: sync Zotero items into normalized JSON, defaulting to the current user's library when possible
- `scripts/export_zotero_items.py`: export library items in BibTeX, CSL-JSON, RIS, or JSON formats
