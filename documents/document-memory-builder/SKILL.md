---
name: document-memory-builder
description: Read a specified set of documents and distill them into a reusable, source-grounded memory pack. Use when Codex is asked to ingest project documents, papers, specs, notes, policies, or mixed corpora and create durable memory artifacts such as canonical facts, terminology, workflows, constraints, entity maps, and open questions for later reuse.
---

# Document Memory Builder

## Quick start

1. Require the document set and intended output location before doing substantive work.
2. Ask for the downstream purpose only if it materially changes what should be remembered; otherwise default to general reusable project memory.
3. Inventory the sources, identify canonical documents, and note recency/version signals.
4. Run `python3 scripts/init_memory_pack.py <memory-name> --path <output-dir>` to create the memory pack scaffold.
5. Read the corpus in priority order, extract durable information, and keep every memory item traceable to one or more sources.
6. Write the pack, explicitly separating stable memory from volatile items and unresolved conflicts.

## Inputs and defaults

### Required

- `documents`: explicit file paths, URLs, or a clearly bounded document set.
- `output_dir`: where the memory pack should be written.

### Optional

- `memory_name`: default to a hyphen-case name inferred from the document set or project folder.
- `purpose`: default to `general reusable memory`.
- `overwrite`: default to `false`. Refuse to overwrite an existing pack unless the user explicitly requests it.

## Output contract

Create one memory directory named after `memory_name` inside `output_dir`:

- `<memory_name>.memory.md`: canonical reusable memory.
- `<memory_name>.source-map.md`: source inventory, authority, and coverage notes.
- `<memory_name>.open-questions.md`: contradictions, gaps, and follow-up questions.

Use the section structure from `references/memory-pack-template.md`.

## Workflow

### 1) Bound the corpus

- Refuse vague scopes such as "read the repo" unless the user explicitly wants that breadth.
- Convert the request into a concrete source list before reading in depth.
- Record document type, path/URL, title if obvious, and any version/date signal.

### 2) Rank sources by authority

Use this default precedence unless the user specifies otherwise:

1. Normative specs, finalized design docs, and authoritative policy documents.
2. Maintained project docs, READMEs, architecture notes, and recent revision plans.
3. Working notes, issue threads, and exploratory drafts.

When two sources disagree, prefer the higher-authority source. If authority is equal, prefer the more recent source. If the conflict remains unresolved, keep both claims in `open-questions` instead of collapsing them.

### 3) Initialize the memory pack

- Run `python3 scripts/init_memory_pack.py`.
- Do not improvise new file names unless the user asks for a different structure.
- If the pack already exists and overwrite is not allowed, update it in place rather than replacing it.

### 4) Read in passes

- First pass: skim every source to understand scope, terminology, and duplication.
- Second pass: read canonical sources closely and extract the durable backbone.
- Third pass: read supporting sources to fill gaps, add examples only when they teach a reusable pattern, and surface conflicts.

Prefer compression over exhaustiveness. The goal is reusable memory, not a complete summary of every paragraph.

### 5) Extract only memory-worthy content

Use `references/extraction-rules.md` when deciding what to keep. By default, preserve:

- Stable facts, definitions, and terminology.
- Enduring project goals, constraints, assumptions, and non-goals.
- Reusable workflows, decision rules, and evaluation criteria.
- Important entities and relationships.
- Recurring pitfalls, caveats, and known failure modes.

By default, do not promote the following into canonical memory unless the user explicitly wants historical detail:

- Transient status updates.
- One-off examples that do not generalize.
- Ephemeral deadlines, owners, or temporary plans.
- Raw quotations without synthesis.

### 6) Keep source traceability

- Every substantive memory item must cite at least one source.
- For local files, prefer `path:line` pointers when feasible.
- For PDFs or documents without stable line numbers, use page/section references.
- If a memory item is inferred from multiple sources, label it as an inference and cite all relevant sources.

### 7) Separate stable memory from volatile memory

In `<memory_name>.memory.md`, keep volatile or likely-to-change items in a short `Change watchlist` section instead of mixing them into stable facts. Examples:

- active milestones
- provisional decisions
- fast-moving metrics
- still-debated terminology

### 8) Write open questions aggressively

Use `<memory_name>.open-questions.md` for:

- unresolved contradictions
- missing definitions
- ambiguous ownership or process
- references to documents that were not provided
- claims that appear important but weakly supported

Do not silently guess when the corpus is incomplete.

### 9) Update behavior

When asked to refresh memory from new documents:

- retain stable sections that still hold
- add new source entries
- revise or retire contradicted items with explicit notes
- preserve prior unresolved questions unless the new corpus resolves them

## Quality bar

- Keep the main memory concise enough to reread quickly.
- Prefer normalized terminology over source-specific phrasing.
- Collapse duplicates across documents.
- Mark uncertainty explicitly.
- Optimize for future reuse by another agent or by the same agent in a later session.

## Resources

- `scripts/init_memory_pack.py`: initialize the standard memory pack directory and files.
- `references/memory-pack-template.md`: required output structure.
- `references/extraction-rules.md`: rules for deciding what belongs in durable memory.
