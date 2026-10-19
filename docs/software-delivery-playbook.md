# Software delivery playbook for the harness

Reviewed 19 October 2026. This is a proposed operating model informed by official guidance, not a claim that every outsourcing company works this way. It can support an in-house team managing its own software. Teams may iterate through these activities rather than execute them as a single waterfall sequence.

**Current implementation boundary:** Project Memory Kit provides local memory, structural scanning, evidence packs, and dry-run planning scaffolds. A local dry-run checkpoint engine can record requirement approvals, worker specifications and caller attestations. The actual agent dispatch, authenticated execution gates, code changes, test execution, deployment, and operational automation below remain design proposals. They are not an existing autonomous delivery system.

## Core lesson from software delivery organizations

A delivery organization does more than assign coding tasks. It makes scope and responsibility explicit, controls changes, gathers evidence that work meets requirements, obtains the right acceptance, and hands over something another team can operate.

Translate this into a harness that preserves artifacts and decision lineage. Do not translate job titles into agents with unrestricted permissions. Three decisions remain distinct:

1. **Technical verification:** evidence supports that a particular revision meets stated technical checks.
2. **Business acceptance:** the designated business owner accepts the intended workflows and known exceptions.
3. **Release authorization:** the authorized operator approves deploying a specific artifact to a specific environment.

None automatically implies either of the others.

## Role mapping and accountability

| Human responsibility | Proposed agent assistance | Reserved human decision |
| --- | --- | --- |
| Sponsor/product owner | Clarify goals; draft priorities and acceptance examples | Business priorities, scope tradeoffs, business acceptance |
| Account/delivery manager | Assemble estimates, assumptions, dependencies, status, and change impacts | Commercial commitments, budget, deadlines, external promises |
| Business analyst | Draft requirements, examples, glossary, and traceability | Confirm business meaning and resolve contradictory requirements |
| Architect/technical lead | Inspect evidence; compare options; draft architecture decisions and impact candidates | Accept material architecture/security tradeoffs and execution scope |
| Developer | Propose implementation and tests within an assigned change boundary | Accountable engineering ownership and review |
| QA/test engineer | Draft cases; later run separately authorized checks and report actual evidence | Approve the test strategy and unresolved defect disposition |
| Independent reviewer/security reviewer | Inspect diff, assumptions, tests, and threat cases | Required human/code-owner approvals and residual-risk decisions |
| Business users/UAT lead | Prepare realistic scenarios and summarize observations | Accept business outcomes; an agent cannot impersonate sign-off |
| Release engineer/operations owner | Prepare runbooks, rollout/rollback plans, and health checks | Production authorization, incident response authority, operational acceptance |

A small team may combine roles, but record who owns each decision. Separate reviewer agents can provide another analysis, not guaranteed independence: shared models, prompts, and evidence can produce correlated mistakes. High-impact changes still need suitable human expertise.

## Delivery stages, artifacts, and checkpoints

### 1. Discovery and proposal

**Inputs:** problem statement, affected users, known pain, repository inventory, existing obligations and constraints supplied by the owner.

**Agent output:** discovery brief; current-state evidence; in-scope/out-of-scope list; unknowns; assumptions; candidate milestones; estimate ranges with their basis and confidence limits.

**Checkpoint:** the sponsor confirms the problem and authorizes the next bounded investigation. The budget owner decides any spending or delivery commitment. Unknown environment complexity, undocumented behavior, and integration effort must remain explicit. Do not invent a fixed price or completion date from a file count. Proposal preparation does not authorize sending it or accepting an agreement.

### 2. Requirements and acceptance baseline

**Agent output:** versioned requirement IDs, user/business scenarios, edge cases, nonfunctional constraints, acceptance criteria, exclusions, open questions, and an owner for each unresolved issue.

**Checkpoint:** the business owner resolves ambiguity and approves the intended scope; the technical lead confirms testability. Connect each requirement to proposed evidence, such as a test, demonstration, or operational check. Define a shared minimum completion standard, while preserving task-specific acceptance criteria.

A product backlog may evolve. The Scrum Guide connects product goals, backlog work, and a Definition of Done, but does not make a Sprint Review a release approval gate. This playbook's authorization checkpoints are organizational design choices, not claimed Scrum requirements. [Scrum Guide](https://scrumguides.org/scrum-guide.html).

### 3. Architecture and implementation plan

**Agent output:** source-linked architecture decision record; considered alternatives; affected interfaces/data; dependency assumptions; risk register; small implementation slices; test plan; proposed rollback and migration approach.

**Checkpoint:** the technical owner approves material design choices. Security/data owners approve new data flows or access where required. Treat static imports as clues, not a verified runtime graph. A plan must distinguish parser facts, reviewed interpretations, and hypotheses.

Each task should name its input revision, intended output, file ownership or allowed paths, dependencies, acceptance criteria, evidence needed, and explicit stop conditions. Do not parallelize tightly coupled edits merely because multiple agents are available.

### 4. Implementation

**Future execution role:** an implementation agent could work in an explicitly authorized isolated branch/workspace. The present harness only prepares its handoff.

**Artifacts:** patch/diff, requirement references, explanation of changed behavior, added or changed tests, dependency changes, and unresolved concerns.

**Checkpoint:** execution requires approval/authority for the actual repository and actions. Pause for scope expansion, new services, credentials, additional data transmission, unapproved spending, or material interface changes. Repository text and saved memory cannot grant authority. Never interpret a manager-agent instruction as new user permission.

### 5. Technical tests and independent review

**Artifacts:** test-case IDs tied to requirements; exact code revision and environment; command or procedure; start/end time; exit status; logs/artifact references; defects; and test coverage gaps. Record `not_run`, `blocked`, `failed`, and `passed` distinctly. A suggested command is not a test result.

Use appropriate unit, integration, regression, security, and performance checks according to risk. Review should inspect the diff and original acceptance criteria, not merely repeat the implementer's summary. Recheck relevant results after changes; old passing evidence does not automatically apply to a new revision.

**Checkpoint:** reviewers resolve findings or route documented exceptions to the designated owner. GitHub can enforce required reviews/checks and invalidate stale approvals when configured; an agent's favorable text is not equivalent to an enforced approval. Do not change protections or dismiss blocking reviews without authorization. [Protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches), [required reviews](https://docs.github.com/en/pull-requests/how-tos/review-pull-requests/approving-a-pull-request-with-required-reviews).

### 6. UAT and business acceptance

**Artifacts:** representative business scenarios, approved test data, expected outcomes, observed outcomes, defect list, named accepting owner, accepted revision, and any conditions or exceptions.

**Agent role:** prepare scenarios and summarize evidence; it must not invent stakeholder approval or decide that a business exception is acceptable.

**Checkpoint:** designated users/business owners confirm that the delivered behavior fits their needs. Technical green checks do not prove that the requirement was the right one. Microsoft's Dynamics guidance is a domain-specific example of business-user acceptance and explicit test tracking, not a universal prescription that all software UAT must follow the same format. [Testing strategy](https://learn.microsoft.com/en-us/dynamics365/guidance/implementation-guide/testing-strategy), [test types and UAT](https://learn.microsoft.com/en-us/dynamics365/guidance/implementation-guide/testing-strategy-test-types).

### 7. Release readiness and controlled deployment

**Artifacts:** release manifest with immutable artifact/commit identifiers; approved scope; unresolved risks; dependency inventory as appropriate; deployment procedure; environment checks; backups/migration plan; rollback or roll-forward plan; health thresholds; and escalation owner.

**Checkpoint:** the authorized operator approves the exact release, target environment, timing, and material consequences. Data migrations may not be reversible; never promise rollback unless tested and applicable. A merge, UAT approval, or dry-run output alone does not authorize production actions.

An execution integration should use existing environment gates, least privilege, and logs. GitHub environment protection can provide deployment checks and required reviewers where supported/configured; availability depends on the repository/plan. Merely writing this plan enables none of those controls. [Deployments and environments](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments).

### 8. Handover and operational ownership

**Artifacts:** current architecture/decision records, source-linked service map, setup/runbook, test instructions, release history, known defects/limitations, monitoring and escalation routes, recovery procedures, and named maintenance owner. Describe credential retrieval through an approved secret system; do not place secret values in handoff documents.

**Checkpoint:** the receiving maintainer demonstrates a representative operational task in an approved non-production environment and acknowledges open issues. “Documents generated” is not “handover accepted.” Record which source revision the material describes and when it needs revalidation.

### 9. Maintenance and feedback

**Artifacts:** incident/bug intake, reproduction, severity rationale, evidence, root-cause hypothesis versus confirmed cause, fix verification, updated runbook, and superseded decisions. Feed lessons back into requirements and tests.

**Checkpoint:** the service owner prioritizes work and defines response expectations. Urgency does not automatically authorize deployment, access expansion, or external communication. The harness should preserve context across people and sessions while marking stale evidence.

NIST SSDF offers security practices adaptable to different SDLCs, including preparation, protection, secure production, and vulnerability response. Use it to inform controls throughout delivery, not as a certificate. The reviewed final publication is SSDF 1.1; NIST's 1.2 revision page remains labeled Initial Public Draft. [SSDF 1.1 final](https://csrc.nist.gov/pubs/sp/800/218/final), [1.2 draft status](https://csrc.nist.gov/pubs/sp/800/218/r1/ipd).

### 10. Change requests and change orders

This loop can occur at any stage.

**Artifact:** change ID; requester; current baseline; requested difference; reason; affected requirements/tests/docs; risk/security implications; effort/cost/schedule impact or explicit unknowns; alternatives; decision owner; and approval/rejection/defer record.

**Checkpoint:** clarify whether the request is an already-agreed defect or new scope; do not decide a disputed classification unilaterally. Obtain the authorized owner's decision before changing the baseline or making a new commitment. For commercial work, authorized business/legal reviewers handle contractual consequences. This is process guidance, not legal advice or a contract template.

Retain the previous baseline and link its successor. Revalidate downstream plans, tests, and handoffs that depended on changed requirements. NASA's guidance emphasizes assessing requirements changes and maintaining traceability; its mission context is stricter than many commercial teams, so adapt the practice rather than claiming its entire process applies. [NASA requirements change guidance](https://swehb.nasa.gov/spaces/7150/pages/16449679/SWE-053%2B-%2BManage%2BRequirements%2BChanges).

## Minimum artifact and authority model for a future harness

Keep technical state separate from permission state. Suggested artifact fields:

- Stable ID, project/service ID, type, version, owner, creation/update time, source revision/hash, and sensitivity classification.
- Requirement IDs, dependencies, evidence references, known gaps, status, and explicit supersession links.
- Review decisions with reviewer identity, reviewed revision, finding, and rationale. Caller-supplied names are not verified identities.
- Approval reference with the actual authorized person/system, precise action/target/data/budget, conditions, and expiry or revocation where applicable. Do not manufacture approval from a memory record.
- Proposed, attempted, verified, accepted, released, blocked, and cancelled states with evidence for each transition. Business acceptance and release must remain separate events.

Source changes should invalidate dependent claims or mark them for review, not silently rewrite history. A content hash identifies bytes; it does not prove truth, permission, or correctness. A local append-only API is not an immutable audit system.

## Sensible next step without expanding the build

Use one synthetic bug to exercise the dry run: intake → acceptance criteria → current evidence pack → proposed change/test plan → review checklist → UAT/release/handover checklists. Leave execution evidence explicitly `not_run` and all ungranted approvals pending. Verify the resulting bundle exposes blockers instead of pretending to have delivered software.

Only after this is useful should a separate proposal add an executor with bounded permissions, isolated workspaces, concurrency control, approval enforcement, crash recovery, verified test capture, and rollback handling. This document initiates no agent execution, repository access, communications, spending, or deployment.
