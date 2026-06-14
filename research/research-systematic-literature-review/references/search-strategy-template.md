# Search Strategy Template

Use this template to document reproducible evidence discovery.

## Search metadata

| Field | Value |
| --- | --- |
| Topic | |
| Domain | |
| Date range | |
| Language | |
| Sources searched | |

## Query ledger

| run_id | date | source | query_string | filters | records_returned | notes |
| --- | --- | --- | --- | --- | ---: | --- |
| run-001 | YYYY-MM-DD | | | | 0 | |

## Deduplication ledger

| step_id | method | input_records | duplicates_removed | output_records | notes |
| --- | --- | ---: | ---: | ---: | --- |
| dedup-001 | exact-title-doi | 0 | 0 | 0 | |

## Zotero library sync

Document Zotero ingestion here when the review uses a Zotero user library, group library, collection, tags, or saved search as a curated source.

| sync_id | date | access_mode | library_type | library_id | collection_key | tags | query | items_retrieved | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | ---: | --- |
| zot-001 | YYYY-MM-DD | api-key / oauth-key / mcp | user / group | | | | | 0 | |

## Version resolution ledger (preprint -> published/venue record)

Use this ledger to resolve preprints (e.g., arXiv/bioRxiv/SSRN) to their peer-reviewed published versions when available. For ML conferences hosted on OpenReview, use the accepted OpenReview forum record as the canonical venue record when applicable (and keep the preprint link only as an access copy). The resolved_publication_url must be the canonical published/accepted record, not the preprint, unless no published/accepted version exists.

| mapping_id | preprint_citation | preprint_id | preprint_url | resolved_published_citation | resolved_publication_url | doi | status | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| map-001 | | | | | | | resolved/unresolved | |

## Coverage notes

- Document search blind spots.
- Document unavailable databases or tool constraints.
- Document mitigation actions.
