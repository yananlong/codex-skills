# Zotero Integration

Use Zotero as a curated discovery or citation-validation source when the user already maintains a relevant library or collection.

## When to use Zotero

- The user already has a curated Zotero library for the domain.
- The task needs to reuse existing collections, tags, or saved searches.
- Another research skill needs citation exports or a curated seed corpus.

## Access modes

- `mcp`: prefer this when the runtime exposes a Zotero MCP server. Use it for interactive inspection of libraries, collections, items, notes, and attachments.
- `api-key`: use the Zotero Web API directly with a personal API key or a read-capable key.
- `oauth-key`: use a key obtained through Zotero OAuth key exchange when the user wants app-mediated authorization rather than manually providing a key.

## Practical guidance

- Zotero Web API v3 is the recommended API version for new development.
- `/keys/current` returns information on the API key provided in the `Zotero-API-Key` header and is the right way to resolve the default user library for a key-backed workflow.
- Treat Zotero as a curated corpus, not as automatic inclusion evidence.
- Still run screening, deduplication, and evidence extraction against the final inclusion criteria in downstream research skills.

## Suggested workflow

1. Resolve the current key via `scripts/inspect_zotero_account.py`.
2. Narrow the scope to a collection, tags, or query when the library is broad.
3. Sync items with `scripts/fetch_zotero_items.py`.
4. Export BibTeX or CSL-JSON only when a downstream tool explicitly needs it.
5. Deduplicate Zotero-derived items against web-discovered records where appropriate.

## Official references

- Zotero Web API v3 basics: <https://www.zotero.org/support/dev/web_api/v3/basics>
- Zotero Web API syncing (`/keys/current`): <https://www.zotero.org/support/dev/web_api/v3/syncing>
- OAuth key exchange: <https://www.zotero.org/support/dev/web_api/v3/oauth>
