# Enterprise pilot: in-house maintenance continuity

Proposal dated 19 October 2026. This is a validation plan, not a statement of enterprise readiness or an authorization to access a company repository.

## Positioning

For software companies maintaining their own products, test whether a source-linked project handoff helps an in-house engineer resume maintenance with less reconstruction and fewer stale-context mistakes. The practical use cases are legacy-system handover, staff rotation, recovery of decision rationale, and continuity when a knowledgeable maintainer is unavailable.

The product supports the company's engineers and existing coding assistants. It does not establish that a team can replace outsourcing, reduce staffing, or autonomously maintain a service. A scanner cannot recover undocumented business intent from syntax alone.

**Initial user:** a maintainer inheriting or periodically returning to a Python service.
**Potential champion:** the technical lead responsible for that service.
**Potential buyer:** the engineering manager accountable for maintenance cost and continuity. Security, repository owners, and procurement may need to approve a pilot.

These buyer roles and the value proposition are hypotheses to verify with interviews.

## Current product boundary

The local prototype stores explicit project decisions, builds a structural source map, refreshes eligible files incrementally, and produces bounded evidence packs and planning scaffolds. It does not run autonomous engineering agents, validate business behavior, execute tests, or make code changes through the scanner. Context budgets currently measure characters; model-token savings and end-to-end productivity gains remain unproven.

The pilot should evaluate this existing boundary. Do not add orchestration, cloud hosting, or enterprise administration merely to make the proposal sound complete.

## Proposed pilot

**Scope:** one company-approved Python service, two weeks, and three to five previously resolved maintenance bugs with known reproductions and acceptance tests. Prefer a service representative of recurring maintenance work, with a reproducible non-production environment. Exclude production incidents, customer data, live credentials, deployment, and changes to production systems.

Before starting, obtain explicit authorization for the specific repository, permitted files, participating people, execution environment, retention period, and any model or third-party destination. A public repository or a synthetic substitute is sufficient for preliminary technical testing. Company-source access is not assumed by this proposal. No company repository has been accessed and no outreach has been sent for this pilot.

### Comparison design

- Baseline: the company's normal maintained documentation, repository search, and existing coding assistant.
- Pilot condition: the same tools, model/version, permissions, and task information, plus Project Memory Kit's current map, decisions, and handoff pack.
- Use matched task variants or different maintainers; counterbalance condition order and task assignment. Avoid having one person solve the exact same bug twice, which would bias the result through memory.
- Keep known fixes hidden from participants while an independent maintainer retains the answer key. Run in isolated copies at the relevant historical revision.
- Record initial setup and scan time separately, but include them in total pilot cost. Measure capture, review, refresh, and correction effort rather than counting only retrieval speed.
- Treat three to five bugs as a feasibility sample, not statistically conclusive evidence. Report per-task results and exceptions, not just a flattering average.

### Measurements

1. **Maintenance effort and cost:** time to the first correct source-backed diagnosis; time to an accepted, tested solution; human review minutes; model usage if any; setup and update overhead. Convert time to cost only using rates supplied by the company, clearly showing assumptions.
2. **Rework and errors:** repeated investigation, incorrect file selection, stale decisions acted on, rejected proposed changes, failed acceptance tests, and regressions. Separate a plausible diagnosis from a verified fix.
3. **Source accuracy and coverage:** proportion of cited excerpts matching the stated revision and hash; relevant-file recall against the maintainer's answer key; unsupported-language and skipped-file coverage; correct abstention when evidence is missing.
4. **Safety:** excluded-path and secret-canary results; unexpected reads/writes/network activity; stale-source rejection; source content appearing in logs or exports; and whether operators followed the agreed permissions. Passing these fixtures is not a security certification.

### Proposed decision gates

Proceed to a larger pilot only if:
- Every emitted source citation matches its claimed bytes/revision, and no stale excerpt is represented as current.
- No unauthorized access, source transmission, or prohibited mutation occurs. Any such event pauses the pilot for review; a secret-pattern test pass does not imply comprehensive prevention.
- Accepted task outcomes and regression results are no worse than baseline, and total maintenance effort shows a promising improvement. Use a provisional target of 20% lower median effort, including tool overhead; report uncertainty and individual-task results.
- The maintainer and technical lead choose to keep using the handoff on subsequent work and can name a recurring problem it solves.

Stop or narrow if ordinary documentation/search is equally effective, update/review overhead consumes the savings, the relevant code is mostly unsupported, stale context still drives errors, or the buyer's real need is autonomous implementation rather than continuity. Any paid continuation requires a separately approved scope and price.

## Enterprise readiness gaps

The local prototype is not an enterprise platform. It lacks SSO, RBAC, authenticated user attribution, tenant security, encrypted storage, managed retention, immutable/tamper-resistant audit records, and a centrally governed access model. Project scoping in a local database is a correctness boundary, not security against someone who can read or edit that database.

Before any live execution integration, separately design and test approval gates, least-privilege access, isolated workspaces, change review, rollback, crash recovery, and evidence of completed verification. The scanner's read-only posture does not supply these controls to another agent. Existing company change-management procedures remain necessary.

A pilot should use the company's approved operating-system, repository, and model controls. That can constrain an experiment; it does not make the prototype compliant, certified, or ready for sensitive multi-user deployment. Do not imply SOC 2, ISO 27001, or any other certification.

## Commercial hypothesis

If the pilot demonstrates recurring net savings, test a fixed-scope paid evaluation or a per-team/per-service support offering. Price should be discovered with the buyer and grounded in observed maintenance value, adoption effort, and support cost. These are possible packaging models, not existing prices, market facts, or revenue forecasts.

Avoid charging for a promise of complete project understanding. A credible deliverable is a documented handoff/evidence workflow with explicit limits and measured outcomes. Define any support obligations, data handling, and licensing separately before a commercial agreement.

## Interview questions

1. Tell us about the last maintenance task delayed because the relevant person or project context was unavailable. What happened, and how much time was actually spent?
2. Which information was missing: source location, system behavior, a business rule, deployment detail, or the reason behind a decision?
3. How do maintainers currently hand over a service, and which parts of that process become outdated?
4. What do your existing coding assistants already handle well? Where have stale context or unsupported assumptions caused rework?
5. Can you provide three to five sanitized, resolved tasks with reproducible tests and a maintainer's answer key?
6. Which source material may be processed locally, which may reach an approved model, and who authorizes that access?
7. Who would review and maintain saved decisions, and how much ongoing effort is acceptable?
8. Which metric would justify adopting this tool? What result would make you reject it?
9. Who owns the budget, security review, and purchase decision? Would a successful pilot have a concrete next step?
10. After seeing measured results, what scoped paid continuation would you consider, and what would you need it to include?

No interviews, external communications, paid services, or signups have been initiated by this document.
