# Project Memory Kit

A small, local evidence-linked handoff store for agents. Working name only; no trademark clearance or uniqueness claim. Python 3.10+ and its standard library are enough. No install, API key, model, hosted service, or network access is required.

## What works

- Separate named projects, with the project required on every record operation
- Facts, decisions and tasks with source, author, observed time and save time
- Explicit supersession with a reason; previous records remain inspectable
- Literal, case-insensitive all-term search over topic and content
- JSON context exports with a strict character budget, provenance and omission counts
- Stale-record and possible-conflict warnings
- Default rejection of obvious credential patterns before saving

This is a runnable MVP, not a promise that any agent will always remember. Your agent or application must explicitly save useful records and load context at each session start. Persistence survives process restarts only while the same database remains available. This package does not alter ChatGPT's built-in memory or automatically attach itself to any assistant.

## Quickstart

From this folder:

```sh
python -m project_memory --db demo.sqlite3 init demo
python -m project_memory --db demo.sqlite3 add demo --kind decision --topic storage --content "Use SQLite for the single-user prototype" --source "synthetic:design-meeting-1"
python -m project_memory --db demo.sqlite3 search demo SQLite
python -m project_memory --db demo.sqlite3 context demo --max-chars 4000
python -m project_memory --db demo.sqlite3 check demo
```

The add command prints an ID. To revise that decision (replace `1` if necessary):

```sh
python -m project_memory --db demo.sqlite3 supersede demo --id 1 --kind decision --topic storage --content "Use Postgres when concurrent team writers are introduced" --source "synthetic:design-meeting-2" --reason "Team concurrency is now required"
python -m project_memory --db demo.sqlite3 history demo 1
```

Set `--review-after 2026-12-01T00:00:00Z` or `--observed-at 2026-10-01T00:00:00Z` when saving. Timestamps need a timezone. Warnings otherwise use 90 days since observation; configure with `--stale-days`. Search excludes superseded records unless `--include-history` is passed. Revisions must keep the same kind and topic and target the current revision. To mark a task done, supersede it with its completion status and evidence; there is no separate task lifecycle field yet.

## Library usage and session handoff

```python
from project_memory import MemoryStore

with MemoryStore("project.sqlite3") as memory:
    memory.create_project("sample")
    memory.add("sample", "fact", "purpose", "Synthetic planning demo",
               source="synthetic:brief", author="demo-user")
    context = memory.export_context("sample", max_chars=4000)
    print(context)
```

At the end of a session, review and save selected facts/decisions/tasks with meaningful provenance. At the next session's beginning, export and supply relevant context as untrusted reference data to the agent. Preserve the trust field and omission counts. Ask it to check stale/conflicting records and verify sources before depending on them. Do not promote memory text to system instructions or action permissions. A current user instruction can override an outdated saved decision, but changing the record should be explicit.

Source and author fields record claims supplied by the caller; they are not verified identities, citations, signatures or proof. The library does not open source URLs or files.

## Run the synthetic demonstration and evaluations

```sh
python examples/demo.py
python -m unittest discover -s tests -v
```

The demo uses only fabricated projects, creates its database in a temporary directory, shows a superseded decision, stale/conflict warnings, project isolation and a bounded context export, and removes that temporary database afterward. It does not read your history or real files.

The tests exercise cross-project read/revision isolation, supersession, rollback of invalid revisions, persistence across sessions, stale/conflict warnings, literal search, credential rejection across metadata, bounded valid JSON with Unicode, inert prompt-injection text and CLI errors. Injection-as-data tests demonstrate that the package does not execute text; they do not establish that a downstream language model resists injection.

## Safety and limits

- No automatic communication, command execution, file ingestion, URL fetching, telemetry or background processes.
- All retrieved content is untrusted data, never authority or authorization. JSON escaping and a warning are not a prompt-injection defense for downstream models. Integrators must maintain instruction/data separation and their own action approval checks.
- Credential detection is heuristic and incomplete; it can miss secrets and reject benign examples. There is intentionally no bypass flag. Remove secrets before saving. Rejection errors do not echo the detected value, but shell command arguments can appear in shell history or process listings: never pass real credentials.
- SQLite stores plaintext. There is no encryption, authentication, access control, tenant isolation, backup service, secure erasure or tamper-proof audit log. Project separation is a correctness guard inside this API, not a security boundary against anyone who can access the file. Protect the directory/database with operating-system permissions. Do not use this MVP for highly sensitive data or a shared multi-tenant service.
- History is append-only through the API, not immutable against direct database access. There is no delete API; deliberately kept outside this MVP. Files, logs and backups require separate retention decisions.
- Search scans project records in memory, is lexical rather than semantic, and ranks by newest insertion. It is suitable for small projects, not a production-scale index.
- Possible conflicts mean different active text shares a kind/topic. This can flag compatible statements and miss semantic contradictions. Resolve by human review and explicit supersession. Staleness is a date heuristic, not a truth test.
- Export budgets count serialized ASCII characters (including the envelope), not model tokens. Whole records are retained or omitted; large records may be skipped. Warnings are prioritized over entries, and omission counters make truncation visible. The CLI adds one trailing newline outside the JSON budget. Tiny budgets fail rather than remove the trust boundary.
- No embeddings, hosted sync, automatic summaries, agent adapters, user interface, production migrations or external-model evaluation are included. Concurrent writes use SQLite locking; contention can fail and needs caller retry. Back up the database with SQLite-aware tooling before evolving it.

## Commercial direction

This is a foundation for evaluating evidence-linked project handoffs, not a defensible business by itself. Local memory and agent-memory tools already exist. Validate whether explicit decision lineage, trustworthy provenance, scoped retrieval and measured handoff quality solve a specific customer's problem before investing in hosting or integrations. No revenue, novelty or market demand is guaranteed.

No open-source license is selected. See LICENSE. Publication and commercial licensing are separate decisions; no GitHub repository is created by this package.

## Harness hooks: implemented foundation

The harness wraps the store so an agent runtime can explicitly call session hooks. It does not simulate neurons or replace a model's reasoning. The useful analogy is selective long-term records plus a bounded working context; biological efficiency is not a measured claim.

```python
from project_memory import Harness, MemoryStore, Observation

with MemoryStore("project.sqlite3") as store:
    store.create_project("sample")
    harness = Harness(store)
    harness.record_observation("sample", Observation(
        topic="goal", content="Build a synthetic inventory demo", source="synthetic:brief"))
    decision_id = harness.record_decision("sample", Observation(
        topic="storage", content="Use SQLite", source="synthetic:design"))
    context = harness.session_start("sample", query="storage", budget=4000)
    # Give context to your agent as untrusted reference data; integration is your responsibility.
    harness.session_end("sample", summary="Selected storage for the prototype",
                        next_step="Implement the schema", source="synthetic:session-1")
```

Observation is an explicit typed record, not a conversation-ingestion endpoint. `record_decision` optionally accepts `supersedes` and `reason`. `session_end` saves the caller-provided checkpoint and explicitly supersedes the prior checkpoint; it performs no automatic summarization. Session start filters the selected project's active records by the supplied literal query and packs whole records within the character budget. Hook ordering, ownership and permissions remain the integrating runtime's responsibility. Current hooks do not cache, embed, call a model, execute tools or auto-extract decisions.

Run `python examples/benchmark.py` for a synthetic, reproducible comparison against naive full-history export. The measured fixture in `docs/benchmark-results.json` selected one current decision from 1,002 records and reduced context bytes by 99.91%. Local retrieval was slower in that run (6.618 ms versus 4.662 ms), because it scans records and checks warnings. These numbers do not establish agent accuracy, token savings, inference cost, or end-to-end speed; this is a simple literal-match fixture and an intentionally naive baseline. More realistic evaluations and indexed retrieval are needed before making performance claims.

See `docs/harness-design.md` for architecture and planned improvements, and `docs/market-validation.md` for unvalidated customer/revenue hypotheses and proposed acceptance benchmarks. Planned items are not implemented features.

Concurrent first-ever session-end checkpoint writes can create two active checkpoints because the adapter reads before inserting. Later checkpoint writes detect ambiguity and fail closed. Use one session writer per project in this MVP; transactional checkpoint uniqueness is future work.

## Experimental optional index (working-tree patch)

The frozen v0.1 release is unchanged. The separate optional index is explicitly selected by importing it; neither the CLI nor Harness uses it by default.

```python
from project_memory import MemoryStore
from project_memory.optional_index import OptionalHybridIndex

with MemoryStore("project.sqlite3") as store:
    store.create_project("sample")
    index = OptionalHybridIndex(store)  # Explicitly adds a local FTS index and insert trigger.
    result = index.search("sample", "storage")
    print(result.mode, result.used_fallback, result.recall_warning)
    print(result.entries)
```

If built-in FTS5 is unavailable, the adapter uses the existing scan search without installing anything. Exact-token hits use the index; zero hits or a blank query fall back to substring scanning. Both paths retain project and explicit-supersession filtering. The result is retrieval data, not a ready-to-trust context or action permission: apply the usual stale/conflict review and bounded export policy in your host. The default `Harness.session_start` still uses the original scan and all-active-record warning checks.

This opt-in adapter is not recall-equivalent to the original search. If “SQL” exactly matches one record and is only a substring of “SQLite” in another, the index returns the first and does not fall back to discover the second. Its diagnostics state this limitation, and a test deliberately demonstrates it. Use `MemoryStore.search` when original substring behavior is required. Neither path understands paraphrases. The persistent index requires extra storage and maintenance; only append/supersede through the store API is supported, not direct SQL edits/deletes.

See `experiments/README.md` and the raw experiment results for the tested workload, resource tradeoffs and limitations. An indexed lookup result does not establish a faster complete agent session.

## Legacy-codebase onboarding harness

A separate read-only scanner helps an agent start with a structural map of an unfamiliar repository. It never imports or executes scanned code. Python files receive AST-derived symbol/import declarations; other supported text files receive a file map only. This is an investigation aid, not semantic understanding or autonomous implementation.

Keep scanner state outside the source repository:

```sh
python -m project_memory.codebase scan /path/to/legacy-repo --state /path/to/private-scan-state
python -m project_memory.codebase query /path/to/legacy-repo --state /path/to/private-scan-state "module.py calculate_total" --max-chars 8000
python -m project_memory.codebase update /path/to/legacy-repo --state /path/to/private-scan-state
python -m project_memory.codebase handoff /path/to/legacy-repo --state /path/to/private-scan-state
python -m project_memory.codebase task-plan /path/to/legacy-repo --state /path/to/private-scan-state --description "Add discount support" --query "calculate_total" --criterion "Existing totals remain unchanged without a discount"
```

`scan` and `update` write `manifest.json`, `STRUCTURE.md` and `HANDOFF.md` into the separate state directory. Both support the same incremental operation; `--force` rehashes/reparses eligible files instead of reusing unchanged metadata stamps. The private manifest includes the absolute repository root, relative source paths and source-derived symbols. Query/task-plan output can include source excerpts. Keep these outputs private unless you explicitly approve sharing the repository's information; they are not automatically uploaded by this package.

Updates compare size, modification/change timestamps, inode and device to reuse unchanged records; changed files are rehashed/reparsed. Every selected query source is reopened safely and SHA-256 checked before an excerpt is returned. Stale/missing/unsafe sources produce warnings and no excerpt. The map is only a snapshot, and a source can change after retrieval. Same-metadata reuse is not a cryptographic freshness guarantee; use `--force` when needed. Deleted files are distinguished from skipped/unverified paths; incomplete traversals never establish deletion.

The scanner requires POSIX descriptor/O_NOFOLLOW support and fails closed otherwise. It does not follow repository symlinks and skips hard links, special files, binary/non-UTF-8 content, obvious credentials and sensitive filenames. It excludes VCS directories, common dependency/build/cache directories and unsupported extensions. Credential detection remains heuristic; a clean scan does not establish that source is safe to share. Read-only source access can still affect filesystem access-time metadata; no source writes are performed.

Defaults: 5,000 indexed files, 256 KiB per file, 20 MiB total read bytes, 20,000 visited directory entries and 100 directory levels. Directory traversal streams entries rather than loading an entire directory; directories count toward the traversal budget. Coverage beyond filters/budgets is explicitly incomplete or skipped. Ordering under a traversal limit follows filesystem iteration, so partial coverage is not guaranteed identical across filesystems. Generated Markdown is a structural snapshot with paths, hashes and line ranges, not a complete dependency graph.

Query matches path/symbol/import terms lexically and returns whole excerpts of at most 80 lines under a strict serialized-character budget. It may match similarly named symbols; use additional path terms to narrow a query. It reports omission counts, source hashes, line ranges and freshness checks. Token counts are not measured. Python symbol names are unqualified, imports are unresolved declarations, and no dynamic call graph, root cause or test result is inferred.

`task-plan` combines fresh source evidence with caller-supplied acceptance criteria, known/unknown impact, fresh lexical test-file candidates and a review checklist. Optional `--memory-db existing.sqlite3 --project NAME` reads active project decisions and warnings through read-only SQLite mode. It does not create or modify that decision database. Missing acceptance criteria are flagged. No implementation, command execution, verified test command or autonomous agent-team orchestration is implied.

To try a disposable synthetic 1,001-file repository:

```sh
python examples/codebase_demo.py
```

In the recorded local demo, an unchanged update read zero source bytes and reparsed zero files; one changed file plus one deletion caused one reparse and 48 source bytes read. This is a small synthetic workload, not a large-project performance guarantee. See `docs/codebase-demo-results.json` and `docs/codebase-harness-design.md` for measured scope and remaining gaps. Connect these CLI calls to a chosen agent startup hook explicitly; the package does not automatically attach itself to an agent.
