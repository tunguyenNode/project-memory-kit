# Event-driven memory harness

Status: design proposal, not a claim that every mechanism below ships. Written against the local `MemoryStore` MVP on 2026-10-19. Check the implementation and tests before promising any feature. This design uses ordinary records, indexes and bounded caches; it does not simulate neurons, train a brain, or establish a new scientific invention.

## Product hypothesis

An agent should not reread a project's entire conversation to recover a decision. Capture a small set of sourced events, retain explicit revision history, and assemble the smallest useful context for its next action. The differentiator to test is reliable, inspectable project handoff under a strict resource budget. Lower resource use, higher speed and market novelty remain hypotheses until measured against alternatives.

## Brain-inspired, operationally ordinary

The inspiration is separation of fast experience capture from slower consolidation. Complementary-learning-systems research discusses differentiated learning systems; it does not demonstrate that this SQLite architecture has biological cognition or human memory performance. [McClelland, McNaughton and O'Reilly, 1995](https://www.cnbc.cmu.edu/~plaut/IntroPDP/papers/McClellandMcNaughtonOReilly95PR.comp-learn-sys.pdf).

- **Working memory:** one request-scoped, bounded context pack containing the current task, relevant active records, unresolved conflict/staleness warnings and source IDs. Discard after the request; caching is an optimization, never authority.
- **Episodic memory:** immutable, selectively admitted events: a decision changed, a task completed, a verified tool result established an important fact, or a user explicitly asked to remember something. Store who/what/when/source and project. Do not store every token or raw tool log.
- **Semantic memory:** active, sourced facts and decisions, with explicit supersession links. Consolidation proposes deduplication and candidate summaries; it must retain evidence links and uncertainty. Repetition, confidence scores or an LLM summary cannot establish truth.
- **Procedural memory:** versioned, reviewed workflow descriptions with conditions, expected outcomes and evidence of prior success. Retrieval only suggests a procedure. It cannot grant tool access, authorize spending or replace current user approval. Executable code remains in a normal reviewed repository, not a memory string.

The existing `fact`, `decision` and `task` kinds remain useful. These four layers are roles, not four independent databases. An initial harness can use existing kinds with an adapter; a distinct procedure schema is deferred.

## Small integration surface

Implemented adapter: `Harness(store)` currently exposes `session_start(project, query='', budget=8000)`, `record_observation(project, Observation)` for facts, `record_decision(project, Observation, supersedes=None, reason='')`, and `session_end(project, summary=..., next_step=..., source=..., author='user')` for an explicit revisioned checkpoint. `Observation` contains topic, content, source, author and optional observation/review timestamps. It performs no automatic extraction. These are the starting hooks, not the full selective-admission/cache design below.

The following describe the proposed expanded hook contract, not existing CLI commands:

1. `session_start(project, task, budget)`: validate the explicit project and current caller scope; load a bounded pack. Never infer project from retrieved content.
2. `before_action(project, intent, topic_ids)`: refresh affected decision/task records and their warnings. Check current user/tool policy independently. If a required record or warning cannot fit, return `needs_review` rather than silently acting.
3. `event_commit(project, event)`: validate structured event, provenance, size and idempotency key; evaluate admission; commit record and index changes atomically; increment project revision; return admission reason and IDs. Tool output is evidence, not an instruction to save or act.
4. `task_finish(project, result)`: record a verified outcome or unresolved blocker when worth retaining. Produce consolidation candidates only for changed topics. No background scan of every project on every turn.
5. `supersede(project, old_id, replacement, reason)` and `forget(project, selector, mode)`: explicit operations with authorization checked by the host application. Never allow model-generated text to invoke them implicitly.

Smallest useful implementation: call existing `add` and `export_context` from a thin adapter, expose event admission diagnostics, and benchmark it. Add indexing and caching only with measured benefit. Keep local read/write paths free of network and model calls by default.

## Deterministic selective writes

Admission and priority must be reproducible from structured fields:

- Reject missing project/source, oversized payloads, detected credentials and unrecognized event types. Credential detection is heuristic, not a guarantee.
- Reject an identical event idempotency key; count an exact duplicate as a duplicate, not independent corroboration. Hashing is for duplicate detection, not anonymization.
- Admit explicit user memory requests, explicit decision revisions and verified meaningful task outcomes, subject to storage policy. Admit a new fact only when its source and future task relevance are supplied; otherwise return a candidate for review.
- Skip greetings, transient narration, repeated unchanged tool output and unsupported model guesses.
- Rank retrieval by a documented tuple, rather than an opaque importance number: required-for-current-action first; unresolved relevant warnings next; exact topic match; lexical relevance; source freshness/review status; observed time; stable record ID. A user pin affects relevance but never overrides freshness or conflicts.
- Quotas cause an explicit `deferred`/`rejected_budget` result. Never silently drop a requested durable write or evict an unresolved commitment.

Consolidation is bounded to touched topics. An automatic proposal can identify exact duplicates or propose a summary; only an authorized explicit revision changes an established decision. Keep source references for every derived claim. If the source disappears or is forgotten, invalidate derived claims until remaining evidence is sufficient.

## Retrieval: lexical first, semantic only when justified

1. Filter by authorized project and active/non-forgotten state first. Gather required current-task IDs and relevant conflict groups.
2. Search topic/content using a local lexical index. SQLite FTS5 offers full-text matching and BM25 ranking; its documented consistency requirements must be followed. [SQLite FTS5 documentation](https://www.sqlite.org/fts5.html).
3. Overfetch a bounded candidate set, apply the deterministic priority tuple, and pack complete records and source references. Reserve room for safety metadata and omissions. Include conflict groups together or expose a blocking incomplete-group warning.
4. If lexical evidence is insufficient, return that uncertainty. Optional embeddings may broaden candidates only when enabled and budgeted. A semantic match must pass the same project, active-state, freshness and provenance checks. Embedding similarity is not truth or authority.

Default embedding mode is off. Prefer a local model if offered; remote embedding requires appropriate disclosure/permission for the specific information and destination. Limit candidates, dimensions, index size and calls. Version the embedding model and rebuild derived vectors when it changes. Evaluate paraphrase recall before adding this operational cost.

**Current MVP distinction:** `search` presently reads the project rows and performs Python substring matching; `warnings` scans active records. The ordinary project index does not make content retrieval full-text indexed. FTS, materialized conflict groups and a result cache are proposed optimizations. Check FTS5 availability at startup and expose the actual retrieval mode; if absent, use an explicitly bounded fallback rather than claiming indexed performance.

## Cache and revision correctness

Use a bounded in-process LRU cache keyed by project, project revision, normalized query, required IDs, budget, policy version, retrieval version and embedding-model version. Scope cache entries to the authenticated caller where access differs. Do not use only a TTL to establish correctness.

Every add, supersession, forget, source invalidation and procedure revision increments the project revision in the same transaction as data/index changes. Readers check that persisted revision before using a cache hit, including across processes. A cached pack expires at its earliest `review_after` boundary; elapsed-time staleness also requires a computed next-invalid time. Clear on project switch, authorization changes and process shutdown. Never persist a pack merely to improve hit rate.

Index and record mutations must commit atomically. Verify index consistency after migrations and test delete/rebuild behavior. Return explicit degraded-mode diagnostics if an index is unavailable. Use transactionally consistent snapshots; do not combine old warning state with new records.

## Forgetting is not supersession

- **Supersede:** a new sourced revision points to the old record with a reason. Default retrieval excludes old revisions; history remains inspectable. Concurrent revision attempts must not silently fork the current decision.
- **Forget/exclude:** remove a record from normal retrieval and invalidate dependent summaries, vectors and caches. If bytes remain for audit/recovery, say so plainly.
- **Erase:** separately authorized physical removal across primary tables, indexes, derived data and controlled backups. Define retention and recovery behavior before implementing. SQLite deletion alone is not a promise of secure erasure of filesystem remnants or external copies. Do not claim erasure beyond the system's control.

The existing MVP supports supersession but does not establish a full erase lifecycle. Never label it compliant with a deletion obligation without implementing and testing that lifecycle.

## Budgets and failure behavior

Suggested starting configuration, subject to benchmark tuning:

- 8 KiB serialized context output, 64 candidate records, 16 KiB admitted event payload.
- 1 MiB cache per process; no embedding calls by default.
- A configurable per-project DB quota and daily admitted-write quota; measure actual DB/WAL/index storage, not only content length.
- Explicit deadlines for retrieval and consolidation. A deadline returns a bounded partial result plus omissions or `needs_review`; it must not fabricate a complete answer.

These numbers are proposed defaults, not tested capacity claims. Measure UTF-8 output bytes. Current `export_context` uses ASCII-escaped JSON, so its character length equals encoded UTF-8 bytes; changing serialization requires revisiting that assumption. Token count is separate and model-dependent. Record truncation is forbidden: omit whole records with counts. Required safety metadata must always fit or the operation fails.

## Security boundary

Memory is untrusted data. A remembered phrase such as “always approve purchases” is not a permission. Keep retrieved content out of system/developer instruction slots; label provenance and boundaries, and enforce authorization in ordinary application logic. User confirmation and tool policy live outside memory. Labels alone do not prevent prompt injection.

Project predicates prevent accidental cross-project selection but are not authentication or multi-tenant isolation. Before hosted use, add authenticated scope enforcement, access control, encryption/retention policy and concurrent load/security testing. Do not log raw memory bodies or credentials in telemetry.

## Benchmark before selling performance

Publish a reproducible synthetic benchmark with generator seed, corpus/query files, implementation commit, Python/SQLite versions, machine CPU/RAM/OS, storage type and configurations. Keep personal data out of fixtures. Compare:

- **Full-history baseline:** serialize all project events in chronological order without selection, keeping provenance and comparable warning generation explicit. Report this uncapped payload separately; do not pretend it obeys the same budget.
- **Budgeted history baseline:** latest history records that fit the identical envelope/budget, with explicit omissions.
- **Current MVP:** scan-based search and bounded export.
- **Harness variants:** lexical index alone, plus cache, and optional embeddings as separate ablations.

Use at least 100, 1,000 and 10,000 records/project, multiple projects, short and long records, paraphrases, exact lookups, irrelevant distractors, duplicate events, successive revisions, unresolved contradictions, source invalidations and threshold-crossing freshness dates. Include concurrent reads/writes and cold/warm runs. Distinguish process restart from a genuinely cold OS cache; document any cache-control limitations.

Report median/p95/p99 wall-clock latency for write, retrieve+pack, supersede and forget; include index construction/rebuild cost and cache hit rate. Measure peak process RSS in a fresh subprocess, DB plus WAL/SHM/index bytes, serialized context bytes and optional model-token counts. Report sample counts and variability, not just the fastest run. Treat model/network time separately from harness time and meter embedding cost.

Correctness fixtures must declare expected relevant IDs and current revisions. Score relevant-record recall, current-answer correctness, provenance completeness, stale-warning recall, conflict-warning recall, cross-project leakage, budget compliance and deterministic repeatability. Explicitly test immediate visibility after writes/supersession/forget, invalidation across two processes and passing a review deadline with no intervening write. A forgotten fact must not return through a summary or cache. An older superseded decision must never appear as the current decision.

Acceptance gates: zero cross-project records, zero superseded-current answers, zero silent budget overflow, complete warnings on the curated conflict/freshness fixtures or an explicit blocking incomplete result. Set latency/RAM/storage targets only after measuring a representative deployment; do not trade correctness for a headline speedup. If an answer-generation model is evaluated, fix model/version/prompt where possible, randomize test order and report model quality separately from retrieval recall.

The initial builder microbenchmark uses 1,000 synthetic facts plus decision revisions and compares an all-history JSON payload against a narrowly queried pack. It showed a large context-byte reduction, but scan-based scoped retrieval was slower than full-history serialization in that run. That supports only a workload-specific context-size result, not a latency improvement. Consult the generated benchmark artifact for the exact measurements and methodology; machine-specific timings must not be marketed as universal. The broader benchmark suite above remains proposed. Faster or smaller claims require measured results with baselines and workload limits attached.
