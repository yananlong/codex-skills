# Zotero Artifact Contract

Use this contract when Zotero outputs are shared with literature-related skills.

## Canonical paths

- `./zotero/zotero-account.json`
- `./zotero/zotero-items.json`
- `./zotero/zotero-sync.md`
- optional:
  - `./zotero/zotero-groups.json`
  - `./zotero/library-export.bib`
  - `./zotero/library-export.csl.json`
  - `./zotero/library-export.ris`

## Required fields in `zotero-items.json`

- `library_type`
- `library_id`
- `resolved_via`
- `collection_key`
- `query`
- `tags`
- `item_type`
- `item_count`
- `items`

## Consumption rules

- `research-systematic-literature-review` should treat `zotero-items.json` as a curated seed corpus, not as automatically included evidence.
- `research-novelty-review` should use it to seed overlap searches and citation checks.
- `research-paper-plan` should use item metadata or exports for citation planning.
- Downstream skills should preserve exact file paths when they consume Zotero artifacts.
