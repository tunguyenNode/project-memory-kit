# Project memory: product opportunity brief

Research date: 19 October 2026. Primary-source documentation review; products were not installed or benchmarked. Feature availability and versions can change.

## Recommendation

Build a narrow experiment: **a portable, local project handoff that shows what is current, why it is believed, and what changed since the last session.** A SQLite CLI is a useful implementation, but is not by itself a defensible product. Sell reduced restart effort and fewer repeated mistakes, if measured, rather than “AI that remembers everything.” Revenue and willingness to pay remain unproven.

## Existing overlap

- **Mem0:** Official materials document memory search with metadata filters, updates by ID, and application-defined version/source metadata. Its official repository also contains a CLI with update, expiration, import, scoped deletion, and latest-version options. Persistence, CRUD, filters, and a CLI are already covered. Source: [programmatic memory management](https://mem0.ai/library/agent-memory/programmatic-memory-management-for-ai-agents-with-mem0), [official CLI source](https://github.com/mem0ai/mem0/blob/main/cli/python/src/mem0_cli/app.py). Platform and OSS behavior must be checked separately; do not generalize one API version's reconciliation behavior to every version.
- **Letta:** Current documentation describes MemFS, a Git-backed memory filesystem with version history, conflict resolution, local-only operation, and deferred loading of deeper reference files. Project initialization and memory audits for duplication and prompt-token usage are documented. This is substantial direct overlap with project persistence, local storage, auditability, and context control. Source: [MemFS](https://docs.letta.com/concepts/memfs), [memory configuration](https://docs.letta.com/configuration/memory).
- **Zep:** Version 4 documents time-bounded facts, invalidation of old facts, and links from derived facts to source episodes. Traceability does not prove truth. Its documentation explicitly says applications must retain retrieved facts and their source records to connect an answer to evidence; API logs are not a complete answer audit trail. Generic provenance and stale-fact handling are already covered. Source: [facts](https://help.getzep.com/v4/facts), [source traceability](https://help.getzep.com/v4/source-traceability). Its separate enterprise dashboard audit feature is not an answer-level evidence trail: [audit logging](https://help.getzep.com/v4/audit-logging).

These sources establish competitive overlap, not that competing products cannot implement the proposed workflow. No exclusive feature gap has been proven.

## Plausible differentiation to test

Package the features around a specific handoff: “Resume this repository in another coding assistant without re-explaining decisions or reviving rejected approaches.”

1. **Decision-specific records:** accepted decisions, rejected alternatives, unresolved questions, next actions, and verification evidence. A claim stores project identity, source reference/hash, recorded time, status, and explicit supersession links.
2. **Deterministic current-state rules:** only explicitly superseded records leave the active view; conflicting unsuperseded decisions remain visibly unresolved. Do not silently choose the newest sentence as truth. Mark changed or missing evidence as needing review, rather than claiming the decision is false.
3. **Reproducible handoff manifests:** record exactly which memory IDs and versions entered each context pack, the budget used, and why records were omitted. This makes a bad handoff inspectable independently of the model provider.
4. **Low-friction portability:** local CLI plus plain Markdown/JSON export; later add adapters only after repeated demand. Avoid requiring customers to replace their agent runtime.

The moat, if one emerges, is trusted workflow integration, a high-quality evaluation corpus, and repeat usage. SQLite, timestamps, secret patterns, or an MCP endpoint alone are readily copied.

## Likely first user and buyer hypothesis

Start with small software agencies or senior developers switching among coding assistants across several long-running repositories. They may lose time reconstructing rationale, repeat failed fixes, or mix client-project context. The individual developer is the likely initial user; an agency owner or engineering lead is a possible buyer if team handoffs measurably improve. These are hypotheses, not validated customer findings. Avoid leading with enterprise compliance: a local database and event log do not establish compliance, tamper resistance, or team access control.

## MVP scope and limits

Implementation note: this brief proposes future validation work. The present MVP does not resolve or hash sources, tokenize context, export handoff manifests, or provide a first-class conflict status. Its implemented budget is serialized characters. Proposed benchmark counts and business targets below are not achieved test results.

Keep the current SQLite CLI scope: add/list/search, explicit supersession, evidence references, scoped context packing, export, and synthetic secret rejection. Add a first-class unresolved-conflict state and handoff manifest before expanding retrieval sophistication. Local storage should mean no network calls in the MVP, not a claim that every downstream assistant keeps exported data local.

Secret detection is a best-effort guardrail. Never claim it catches all credentials. Test database files, journals, logs, errors, and exports for accidental retention; do not store rejected secret text in audit events. Project scoping is not an OS security boundary against someone who can read the database. An append-only application log is not tamper-proof if the database owner can edit it.

## Three acceptance benchmarks

These are proposed release gates, not achieved results.

1. **Correctness, freshness, and evidence:** Use 40 hand-authored fixtures across four projects, including 10 supersession chains, 10 unresolved conflicts, and 10 changed/missing sources. Every current-state answer must select the expected active record or expose the conflict; zero superseded records may appear as current; every selected claim must have a resolvable evidence reference or an explicit unavailable-evidence warning. Preserve full supersession history.
2. **Isolation, rejection, and budget:** Run 100 adversarial cross-project queries and 50 synthetic credential fixtures. Require zero out-of-scope records in output and zero rejected credential strings in the database, journal, logs, errors, or exports. Test 100 context packs at declared budgets of 256, 1,024, and 4,096 tokens: none may exceed the selected tokenizer's limit; identical state and query must yield identical packs. Report secret-test coverage and tokenizer identity rather than claiming universal protection.
3. **Measured handoff value:** With five consenting developers, run two matched resume tasks each, counterbalancing a maintained Markdown handoff baseline against this tool with the same model and task information. Target at least 30% lower median time to the first correct project-specific action, with no increase in stale-decision errors. Separately log capture/review effort so onboarding work cannot hide the true cost. This small pilot is directional, not statistical proof.

## Validation plan and decision gates

- Conduct 8–10 interviews focused on the most recent real restart failure: what was forgotten, time lost, current workaround, assistant switching, and who would pay. Ask to see a sanitized example rather than relying on enthusiasm.
- Compare against a good maintained Markdown project handoff, not only an empty-context strawman. If possible later, benchmark configured competitors on the same cases; no competitor performance claim is justified yet.
- Run the five-developer pilot above over two weeks. Look for voluntary repeated use and whether capture overhead erases retrieval savings.
- Only after demonstrated value, test an explicitly priced paid pilot. Pricing is a hypothesis to discover, not infer from competitor popularity. No outreach, signup, or payment has been performed for this brief.
- Continue if the benchmark passes, at least three pilot users independently keep using it, and at least two buyers express concrete willingness to pay at the tested price. Otherwise narrow the workflow or stop before adding hosted infrastructure.

## Important unverified assumptions

Users regularly switch assistants; restart pain is frequent enough to pay for; they will capture decisions or approve extracted ones; local-only ownership is valuable; integrations can fit their workflow; and deterministic records beat well-maintained Markdown for this job. None of these follows from vendor documentation. Native agent memory may improve faster than an independent tool, and competitors can reproduce the feature bundle. Validate the specific workflow advantage before treating this as a business.
