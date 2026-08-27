# Skills Catalog

Generated from `**/SKILL.md`. This is an open catalog: new skills are included by rerunning `scripts/generate_skill_catalog.py`.

- Skill count: 20
- Domains: commercialization, documents, research, writing

| Domain | Skill | Primary intent | Capabilities | Path |
|---|---|---|---|---|
| commercialization | `commercialize-academic-research` | analysis | commercialization, stage-routing | `commercialization/commercialize-academic-research` |
| commercialization | `market-patent-diligence` | review | commercialization | `commercialization/market-patent-diligence` |
| documents | `adversarial-doc-review` | review | literature-review, paper-review, stage-routing | `documents/adversarial-doc-review` |
| documents | `document-memory-builder` | analysis | document-memory | `documents/document-memory-builder` |
| documents | `exposition-to-notebook` | execution | notebook-generation | `documents/exposition-to-notebook` |
| documents | `pdf-book-assembler` | execution | pdf-processing | `documents/pdf-book-assembler` |
| documents | `proportional-pdf-trimmer` | specialized-workflow | pdf-processing | `documents/proportional-pdf-trimmer` |
| research | `research-experiment-plan` | planning | experiment-design, research-planning, stage-routing | `research/research-experiment-plan` |
| research | `research-idea-discovery` | ideation | experiment-design, ideation, literature-review, novelty-review, research-planning, stage-routing, ... | `research/research-idea-discovery` |
| research | `research-novelty-review` | review | novelty-review | `research/research-novelty-review` |
| research | `research-paper-plan` | planning | paper-planning, paper-review, research-planning, results-audit, stage-routing | `research/research-paper-plan` |
| research | `research-paper-review` | review | multi-agent, paper-review | `research/research-paper-review` |
| research | `research-pipeline-planner` | orchestration | ideation, literature-review, novelty-review, rebuttal, research-planning, stage-routing | `research/research-pipeline-planner` |
| research | `research-rebuttal` | review | paper-review, rebuttal, research-planning | `research/research-rebuttal` |
| research | `research-results-auditor` | review | results-audit, validation | `research/research-results-auditor` |
| research | `research-review-loop` | review | results-audit, technical-writing | `research/research-review-loop` |
| research | `research-systematic-literature-review` | review | literature-review, novelty-review, validation | `research/research-systematic-literature-review` |
| research | `research-zotero` | execution | literature-review, novelty-review, zotero | `research/research-zotero` |
| writing | `prose-flow-improver` | revision | multi-agent, technical-writing | `writing/prose-flow-improver` |
| writing | `technical-writing-reviser` | revision | document-memory, multi-agent, research-planning, results-audit, technical-writing | `writing/technical-writing-reviser` |

## Extension Points

- Add a new skill folder with `SKILL.md`; the generator discovers it automatically.
- Add optional `catalog.json` beside `SKILL.md` when inferred metadata needs correction or enrichment.
- Do not treat `domain`, `primary_intent`, or `capabilities` as closed enums; downstream tools should tolerate new values.
