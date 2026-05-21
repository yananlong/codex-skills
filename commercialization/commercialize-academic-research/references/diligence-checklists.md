# Diligence Checklists

Use only the sections that affect the decision. These checklists are forcing functions, not a script to dump into every answer.

## Framework anchors

- NSF I-Corps: immersive commercialization training that pushes researchers beyond the lab toward customer discovery and invention-to-impact work: https://www.nsf.gov/funding/initiatives/i-corps
- DOE Adoption Readiness Levels: complements TRL by surfacing market and adoption risks across value proposition, market acceptance, resource maturity, and license to operate: https://www.energy.gov/technologycommercialization/adoption-readiness-levels-arl-framework
- Stanford Biodesign: need-driven health innovation process organized around identify, invent, and implement, with attention to unmet needs, IP, regulatory, reimbursement, market potential, and funding: https://med.stanford.edu/biodesign/about-us/process.html
- NIH SEED/SBIR-STTR: product development and commercialization support for small-business biomedical innovation: https://seed.nih.gov/

## I-Corps-style discovery

- State each hypothesis before the interview: customer, pain, workaround, buyer, channel, revenue model, partner, resource requirement.
- Ask for concrete recent behavior: last time the problem occurred, workaround used, cost, owner, and consequence.
- Separate users from buyers and partners from customers.
- Require a next commitment for strong evidence: introduction, data access, paid discovery, LOI with criteria, pilot budget, or procurement step.
- Update the hypothesis ledger after each learning loop.

## Pricing and willingness-to-pay

- Anchor price to the customer's current cost, not the research team's effort.
- Test budget source and approval threshold before asking for a target price.
- Prefer tradeoff questions: what would they stop buying, defer, or reallocate to pay?
- Distinguish ability to pay, willingness to pay, and authority to pay.
- Treat unpaid pilots as learning tools only when conversion criteria and economic buyer are explicit.

## Regulated, health, and clinical diligence

- Identify whether the buyer is a provider, payer, life-science company, patient, employer, lab, manufacturer, or public agency.
- Map user, patient/beneficiary, clinician/operator, buyer, reimbursement owner, privacy/security gate, and regulator.
- Check regulatory class/pathway, clinical evidence burden, reimbursement or coding path, privacy/security requirements, workflow integration, liability, and post-market obligations.
- In health, start from an observed unmet need and care/workflow economics; do not start from the device, model, or assay novelty.
- A clinical pilot needs success metrics, patient/data access, IRB or compliance path if applicable, workflow owner, and adoption decision after the pilot.

## TTO, IP, and freedom-to-operate

- Confirm invention disclosure, ownership, sponsor obligations, publication timing, patent status, and field-of-use constraints.
- Ask whether the university TTO, inventors, and potential licensee/startup agree on the commercialization route.
- Patentability can support defensibility, but FTO, implementation know-how, data, regulatory execution, and distribution often decide value capture.
- For open-source software, datasets, biological materials, and tangible research property, check licenses, MTAs, data-use rights, privacy, and redistribution limits.

## Validation sprint design

- Define one decision per test: continue, pivot, kill, or defer.
- Prioritize tests that retire the weakest link in the required chain.
- Make pass/fail criteria observable before running the test.
- Keep tests cheap: interviews, desk diligence, mock procurement, workflow shadowing, retrospective cost model, prototype task test, partner diligence, paid discovery, or technical replication.
- Do not call it a pilot unless buyer, budget, success metric, timeline, data/integration access, and conversion step are known.

## Adversarial review

- What claim is being treated as fact without evidence?
- Where is the plan confusing user, buyer, operator, procurement, regulator, or beneficiary?
- What is the current workaround, and why is it good enough?
- What must be true for the recommended path to beat licensing, partnership, or services?
- Which assumption could invalidate the plan fastest?
- What is the cheapest test that could produce a negative answer?
- Is "platform" being used to avoid choosing a painful wedge?
- Is "pilot" being used to avoid price, procurement, or deployment proof?

## Manual eval prompts for this skill

1. Software: "Commercialize a university lab's open-source static-analysis tool that finds race conditions in Rust services with 20% fewer false positives than prior benchmarks."
2. Biotech: "Assess commercialization paths for a CRISPR delivery nanoparticle with promising mouse data but no large-animal or tox package."
3. Health AI: "Red-team a plan to sell an ML triage model to emergency departments based on AUROC gains in a retrospective paper."
4. Materials: "Find a beachhead for a low-temperature ceramic coating that improves corrosion resistance in lab salt-spray tests."
5. Climate/energy: "Evaluate a solid sorbent carbon-capture material from a national lab with strong adsorption but unknown regeneration cost."
6. Robotics: "Commercialize a manipulation policy that improves bin-picking success in cluttered benchmark scenes."
7. Data asset: "Assess a rare-disease imaging dataset and benchmark as a commercialization opportunity."
8. Agriculture: "Compare licensing versus startup for a sensor that detects crop nitrogen stress earlier than current handheld tools."
9. Vague input: "We have a novel AI algorithm from a paper and want a startup idea."
10. Plan review: "Red-team this claim: the market is huge, pharma companies need better simulation, so we should build a platform and run free pilots."

## Output regression checks

- Evidence separation: sourced facts, user-provided facts, inferences, and speculation are labeled.
- Buyer/user distinction: user, buyer, budget owner, operator, procurement/compliance, and beneficiary are not conflated.
- Non-generic wedge: recommendation names a workflow, buyer-owned metric, current workaround, and proof milestone.
- Path comparison: startup is compared against licensing, partnership, service, component/tooling, or data-asset routes.
- Risk rigor: weak link and cheapest next test are explicit for every major recommendation.
- Validation specificity: interviews, pilots, pricing tests, and diligence tasks have pass/fail criteria and decisions informed.
- Anti-overclaiming: no invented market facts, unsupported TAM, fake pilot advice, or academic-novelty-as-demand logic.
