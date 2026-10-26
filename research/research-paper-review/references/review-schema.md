# Review Schema and Conversion Table

One issue schema and one summary schema serve `research-paper-review`, `research-review-loop`, `research-rebuttal`, and the planner's review stage. `scripts/review_schema.py` reads every known layout into them, keeps every unmapped field under `extra`, and records which layout and which aliases it used. It never writes files. The same module ships, byte-identical, in the review-loop and rebuttal skills.

## Canonical issue

The canonical issue is the review-loop issue object, so a `REVIEW_STATE.json` written by `init_review_loop.py` is already canonical.

| Field | Type | Notes |
| --- | --- | --- |
| `id` | string | Stable across rounds. Importers keep incoming IDs and mint `PR<n>` only when one is missing. |
| `title` | string | Required for an open issue. |
| `severity` | `major`, `moderate`, `minor` | Required for an open issue. Derived from a 1-5 `impact_rating` when absent (4 or 5 major, 3 moderate, 1 or 2 minor). |
| `impact_rating` | integer 1-5 or null | |
| `confidence_rating` | integer 1-5 or null | |
| `status` | `open`, `resolved`, `accepted` | Implied by the list that holds the issue when the issue does not say. |
| `evidence` | string | |
| `required_action` | string | |
| `source_quote` | string | Exact quote from the reviewed artifact. |
| `source_section` | string | Section, table, figure, file, or line range. |
| `related_sections` | list | |
| `origin` | string | Where the issue came from. |
| `resolution` | string | How a resolved or accepted issue was closed. |
| `comment_type` | string | Paper-review comment type or rebuttal category. |
| `prior_issue_ids` | list | Earlier or internal IDs this issue continues. |
| `extra` | object | Source fields the schema does not name, kept verbatim. |

A resolved or accepted entry that holds only an `id`, a `status`, and a `resolution` is a reference to an earlier issue. The normaliser fills its title and severity from another entry with the same ID when one exists, and otherwise records it as a closed reference, never as an error.

## Canonical summary

`review_summary.json` keeps its current shape. Required: `overall_paper_rating`, `decision_relevance_rating`, and `rating_confidence` (integers 1-5), and `top_blockers` (a list). Optional fields stay as they are, including `execution_mode`, `fallback_reason`, `depth`, `workers_used`, `context_artifacts`, the context and novelty ratings, and `issue_counts`.

## Conversion table

| Canonical field | Also read from |
| --- | --- |
| `id` | `issue_id` |
| `title` | `issue`, `risk`, `name` |
| `severity` | `priority`; values `critical`, `blocker`, `blocking`, `high`, and the rebuttal board's `Major-Blocking` and `Major-Addressable` map to `major`, `medium` to `moderate`, `low`, `nit`, `trivial`, and `Misunderstanding` to `minor`; else a 1-5 impact rating |
| `impact_rating` | `impact`, `impact_score` (integer 1-5 only; prose is dropped) |
| `confidence_rating` | `confidence`, `confidence_score` |
| `status` | `state`; `closed`, `fixed`, `addressed`, `reframed`, `superseded` map to `resolved`; `accepted_risk`, `wontfix` to `accepted`; `deferred`, `partial`, `in_progress` to `open` |
| `evidence` | `explanation`, `rationale`, `problem` |
| `required_action` | `required_fix`, `fix`, `recommendation`, `suggested_fix` |
| `source_quote` | `quote` |
| `source_section` | `section`, `location`, `lines` |
| `origin` | `source` |
| `resolution` | `closure`, `acceptance_rationale` |
| `comment_type` | `category`, `kind` |
| `prior_issue_ids` | `predecessor_id`, `supersedes`, `internal_issue_ids` (a comma-separated string becomes a list) |
| summary `overall_paper_rating` | `overall_score_1_to_5`, `overall_rating` |
| summary `rating_confidence` | `confidence_score_1_to_5`, `overall_confidence` |
| summary `top_blockers` | `top_open_issue_ids`, `blockers` |
| summary `novelty_decision_rating` | `novelty_score_1_to_5` |
| summary `issue_counts` | `open_issue_counts_by_severity` |

## Issue layouts

| Layout | What it is |
| --- | --- |
| `paper_review_native` | `final_issues.json` array with 1-5 impact and confidence ratings |
| `openaireview_claude` | `final_issues.json` array with severity tiers and no ratings |
| `issue_list_aliased` | an issue array that needed the aliases above |
| `review_loop_state` | `REVIEW_STATE.json` with `open_issues`, `resolved_issues`, `accepted_risks` |
| `review_loop_state_extended` | a state whose issues also or only live in other lists (`issues`, `tracked_issues`, `deferred_issues`, `carried_*_issues`, `resolved_or_reframed_issues`); the list name stays in `extra.source_list` |
| `review_state_without_issues` | a state that records a verdict but no issue lists |
| `rebuttal_issue_board` | the rebuttal `issue-board.md` table; Notes becomes the title, Strategy the required action, Internal issue IDs the prior IDs |

## Validators

- `research-review-loop/scripts/validate_review_state.py` checks a state. The default mode reads any layout above: aliases, extra lists, closed references, and missing top-level fields are warnings, and an open issue without a title or severity, a duplicate ID within one list, or an unknown status is an error. `--strict` requires the canonical schema exactly and is what every new round must pass.
- `scripts/validate_review_bundle.py` reads summaries through the same module, so aliased summary keys count.
