# Source Taxonomy

Use this taxonomy to decide what a source can prove. Do not treat all sources equally.

## Reliability labels

- `high`: official patent-office record, government regulator/procurement/funding page, public-company filing, standards body record, customer-visible product/pricing page, or directly cited primary document.
- `medium`: company press release, credible industry database, reputable trade publication, conference/company presentation, or customer case study.
- `low`: unsourced market report excerpt, generic blog post, aggregator snippet, venture database blurb, press article without primary evidence, or AI/search summary.

## Patent and IP sources

Use multiple sources when patent conclusions matter.

- USPTO Patent Public Search: U.S. patents and patent application publications.
- USPTO Assignment Center: recorded assignments and ownership-change signals.
- USPTO Global Dossier / Patent Center: family/file-wrapper and prosecution-context signals when accessible.
- WIPO PATENTSCOPE: published PCT applications, participating national/regional patent documents, and some non-patent literature.
- EPO Espacenet: broad patent publication discovery, patent families, classification help, and competitor/technology tracking. Do not scrape it; use EPO OPS for automated retrieval.
- EPO Register, national registers, and INPADOC/legal-status sources: legal-status signals, subject to coverage and interpretation limits.
- Google Patents, Lens, or Semantic Scholar: useful discovery and citation leads, but confirm important records in patent-office or registry sources.

## Market, competitor, and buyer sources

- Company product pages, docs, pricing pages, demo pages, customer case studies, support docs, and security/compliance pages: strongest public evidence for current offerings and target users.
- SEC EDGAR 10-K/10-Q/S-1/20-F/investor presentations: public-company revenue segments, risk factors, customer concentration, product lines, and strategy signals.
- Procurement and spend sources such as SAM.gov, USAspending.gov, EU TED, state/local procurement portals, and agency forecasts: evidence of public-sector demand and buying language.
- Grants and translational funding sources such as Grants.gov, NIH RePORTER, NSF awards, SBIR/STTR databases, ARPA-E/DOE award pages, BARDA, DARPA, and regional innovation programs: evidence of funded problems, not necessarily commercial demand.
- Regulator and reimbursement sources such as FDA, CMS, EMA, MHRA, EPA, FCC, FAA, NHTSA, USDA, and equivalent agencies: adoption constraints and evidence burden.
- Standards and certification sources such as ISO, IEC, IEEE, ASTM, UL, NIST, HL7, FHIR, SOC 2, HIPAA guidance, and sector-specific bodies: implementation and procurement gates.
- Customer forums, job postings, RFPs, manuals, and workflow documentation: useful workaround and pain signals, but verify before treating as buyer evidence.

## Evidence strength rules

- A patent proves a publication or filing event; it does not prove demand, enforceability, blocking scope, validity, or freedom to operate.
- A press release proves the issuer said something; it does not prove adoption, revenue, performance, or willingness to pay.
- A public filing is strong for what a company reported, but may aggregate segments and omit early products.
- A procurement notice proves a buyer or agency described a need or purchase process; it does not prove sustained market demand.
- A grant or award proves funding interest; it does not prove customer pull or post-grant adoption.
- A clinical trial or regulatory clearance can prove evidence generation or permission to market; it does not prove reimbursement, workflow adoption, or budget.
- A market report is only decision-useful when the methodology, segment definition, and buyer relevance are clear.

## Source-log minimum fields

| Date | Query/source | Source class | Claim supported | Key observation | Reliability | Limitation | Follow-up |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  | high / medium / low |  |  |
