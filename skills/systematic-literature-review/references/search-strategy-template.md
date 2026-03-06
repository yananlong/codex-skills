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

## Version resolution ledger (preprint → published/venue record)

Use this ledger to resolve preprints (e.g., arXiv/bioRxiv/SSRN) to their peer-reviewed published versions when available. For ML conferences hosted on OpenReview, use the accepted OpenReview forum record as the canonical *venue* record when applicable (and keep the preprint link only as an access copy).

| mapping_id | preprint_citation | preprint_id | resolved_published_citation | doi | status | notes |
| --- | --- | --- | --- | --- | --- | --- |
| map-001 | | | | | resolved/unresolved | |

## Coverage notes

- Document search blind spots.
- Document unavailable databases or tool constraints.
- Document mitigation actions.
