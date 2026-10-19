# Codebase onboarding without rereading everything

## Goal and scope

Help an agent resume work in an unfamiliar or legacy repository by recovering a small, source-linked structural map, then opening the few relevant current files. The harness should avoid repeatedly placing the entire codebase into a model context. It is not a replacement for reading the code relevant to an actual change.

This document distinguishes a local structural-index foundation from the broader product design. No real customer repository or private data was used to develop this proposal. No code execution, runtime tracing, automatic bug diagnosis, or verified architectural understanding is implied by a scan.

## Status

The working-tree implementation now includes `project_memory/codebase.py`. Run `python -m project_memory.codebase` for its current CLI. Implemented commands are `scan`, `update`, `query`, `handoff` and `task-plan`, with an explicit repository root and required `--state` directory outside the repository. This document is a design boundary, not a test-completion certificate.

Implemented scanner behavior:

- Local manifest plus `STRUCTURE.md` and `HANDOFF.md`; no source imports, test runs or application execution.
- Python AST function/class names and source spans, plus import declarations. Names are not fully qualified and imports are not resolved. Other accepted text languages receive file-level metadata only.
- Default caps: 5,000 indexed files, 262,144 bytes per file, 20,971,520 bytes read per scan and 20,000 encountered directory/file entries, with directory nesting capped at 100. Traversal streams rooted file-descriptor `scandir` entries rather than materializing directory listings. Excluded directories are pruned, so path counts are not the entire repository inventory. Each read is capped by the smaller of the file limit and remaining total-byte allowance; failed-read bytes count against that allowance.
- Reuse based on size, modification/change times, inode and device. `--force` rehashes eligible files; selected query candidates are always reread and rehashed before excerpts are returned. Metadata reuse is not cryptographic freshness.
- POSIX descriptor-based `O_NOFOLLOW` reads, single-link regular-file checks, filename/directory exclusions, UTF-8/NUL checks and heuristic credential-pattern rejection. Unsupported platforms fail closed. This does not establish a complete adversarial-filesystem sandbox.
- Explicit added/changed/removed and not-indexed-or-unverified sets. Limited traversal does not imply deletion; deletion checks use safe metadata-only inspection. Parser failures produce unknowns instead of retained current symbols.
- Bounded lexical query over paths/symbol names/imports, returning up to 80 source lines per selected excerpt with hashes, locations, omissions and stale-source warnings. Defaults are 8,000 serialized ASCII characters and 10 candidate results. Empty source excerpts have `empty_source=true` and null line ranges. These are source excerpts, not structural metadata alone; treat them as private until reviewed for sharing.

Implemented task scaffold: `task_plan(root, state, description, query_text, criteria=None, max_chars=16000, memory_db=None, project=None)`. CLI: `task-plan ROOT --state DIR --description TEXT --query TERM`, with repeatable `--criterion TEXT`, optional `--max-chars N`, and optional `--memory-db DB --project NAME`. It assembles freshly checked source candidates, caller-provided criteria, known-versus-unknown impact and lexical “test” candidates. An optional existing memory database is opened using SQLite read-only mode to retrieve active decisions and warnings. It does not edit code, execute commands, verify tests or establish that suggested test files cover the feature.

The local manifest records the absolute root for identity checking; generated state is not automatically safe to publish. Review paths, filenames, structure and excerpts before sharing. No hosted authentication, full dependency resolver, semantic diagnosis, automatic architecture summary, atomic multi-artifact snapshot or multi-agent executor is established by these features. Sections below describe the intended contracts and roadmap where they go beyond this implementation.

## User workflow

1. **Select a repository and project explicitly.** Show the selected root and scan policy. Read locally within that root; do not upload repository contents or call a remote model merely to index them.
2. **Build an initial map once.** Inventory eligible paths; extract bounded structural facts from supported files; retain source paths, content hashes and symbol locations. Report scan coverage, skips and errors before showing a map.
3. **Start the next session from a handoff.** Return repository identity, scan freshness, relevant symbols/import relationships, unresolved questions and source references in a bounded payload. The model sees evidence, not a confident invented architecture narrative.
4. **Refresh before relying on the map.** Detect changed, added and removed files according to the manifest policy. Re-extract only affected structural records; invalidate records that are no longer backed by the current file. A metadata shortcut must not claim content-level verification.
5. **Investigate a bounded question.** For a question such as “Where is request validation handled?”, retrieve candidate paths and symbols. Have the agent open those current source ranges and nearby callers/configuration before forming a diagnosis. A literal search can miss a synonym; an empty result means no indexed match, not that a feature does not exist.
6. **Save a useful handoff.** Record an explicit, sourced explanation or confirmed decision after the work. Separate human/agent interpretation from parser-extracted structure and runtime observations. Each remains revisable when evidence changes.

This avoids repeatedly reading all source into the model. It does not eliminate filesystem I/O: a correctness-first hash refresh may still read every eligible file to find changes. Distinguish fewer model-input bytes, fewer AST parses and fewer filesystem reads in measurements and product copy.

## Feature-task intake and implementation handoff

The planning role is to carry the right evidence between sessions and agents. It is a scaffold for reasoning, not an autonomous code writer or a guarantee that a proposed change will work.

1. **Task:** capture the caller's feature request, explicit acceptance criteria and constraints. Label missing criteria as unresolved; do not invent stakeholder agreement.
2. **Evidence and constraints:** retrieve current source-linked candidates plus applicable recorded decisions. Check manifest freshness and coverage; a remembered instruction cannot grant authority.
3. **Impact candidates:** list potentially affected files/symbols with match reasons and evidence. These are candidates, not an exhaustive change set or verified dependency closure. Distinguish parser facts from proposed design choices.
4. **Acceptance and test plan:** preserve the caller's criteria verbatim where appropriate. Suggest tests tied to each criterion, record assumptions and indicate what needs inspection. Existing test filenames do not prove tests cover the feature. Suggested commands remain unexecuted.
5. **Implementation-agent handoff:** deliver the bounded task, evidence references/hashes, constraints, candidate changes, test suggestions and unresolved questions. The receiving agent must inspect current source and obtain any needed execution/change permissions independently.
6. **Refresh after work:** record actual changed paths, explicit decisions and observed verification results with sources. Rescan affected code and invalidate stale structure/derived plans. Separate a proposed command, an attempted run and a successful verified test result.

The implemented `task-plan` operation assembles caller-supplied criteria and source candidates without an LLM. Its result should plainly say `planning scaffold` and `tests not run`; if no evidence matches, it should keep the unknowns visible. Architecture decisions, implementation code and test execution remain separate workflows. Do not market a deterministic template as validated feature planning or automatic root-cause reasoning.

## Evidence model

A structural fact should carry project/repository identity, relative path, file content hash, extractor version, extraction time, fact kind, location and extraction status. Prefer stable names plus a source hash over a bare line number; lines shift after edits.

Useful fact categories:

- **Inventory:** an eligible file was observed at a path at scan time.
- **Symbol:** the parser found a function/class definition with its qualified name and source span.
- **Import declaration:** the source contains an import statement. This is a syntactic dependency clue.
- **Resolved local import:** a resolver maps a declaration to a specific local file under documented package/search-path assumptions. This is a separate derived claim, not an automatic consequence of seeing an import.
- **Interpretation:** a reviewed description of subsystem responsibility, with supporting source references and unresolved assumptions.

Python's AST interface provides parsed syntax trees. Parsing does not establish runtime behavior, and successful AST parsing alone does not guarantee executable valid code. [Python AST documentation](https://docs.python.org/3/library/ast.html).

Do not present import declarations as a complete call graph. Relative imports, namespace packages, path mutation, plugins, dynamic imports and framework wiring can defeat simple resolution. A module imported under a type-checking guard may not load at runtime. Label edges with a categorical basis such as `syntax_observed`, `locally_resolved_under_assumptions`, or `runtime_verified`; never invent numeric confidence. Do not assign the last label without separate authorized runtime evidence.

## Partial coverage is a first-class result

A scan can be useful without being complete, but every handoff must make its limits visible. Ideally retain per-scan counts for discovered paths, eligible files, unchanged files, parsed files, unsupported files, skipped files, failed files and records omitted from the context pack. Counts must have clear denominators: hitting a traversal cap means total repository size may be unknown.

Distinguish these cases:

- Explicit policy exclusions, including secret-prone paths, generated/build outputs and dependency/vendor directories.
- Symlinks, special files, binary content, unsupported encodings or unsupported languages.
- File-size, file-count, traversal, time or output-budget limits.
- Permission errors, disappearing files and parser errors.
- Unsupported dynamic behavior, even when every Python file parses successfully.

A file with a syntax error is present but unparsed. A file hidden beyond a scan cap is unobserved, not deleted. Unsupported JavaScript or configuration may contain the actual behavior; do not generalize a Python-only map into a complete repository architecture. “Complete scan” can only mean complete under an explicit selection policy and successful traversal, not complete program understanding.

## Incremental refresh and invalidation

Use content hashes to associate extracted facts with exact bytes. Record extractor/schema versions so a parser change can force re-extraction even when source bytes are unchanged. An mtime/size shortcut is cheaper but can miss same-size edits or restored timestamps; if offered, disclose its weaker freshness guarantee.

A proposed refresh transaction:

1. Establish a scan generation and inventory under the chosen root/policy.
2. Read bounded file bytes safely; hash and parse those same bytes so provenance cannot point to a different read.
3. Keep unchanged facts; replace changed-file facts with successful new extraction. If extraction fails, mark the prior facts stale/unavailable rather than presenting them as current.
4. Remove or tombstone facts for confirmed-deleted files. Do not infer deletions from a partial/failed traversal.
5. Invalidate dependent local-import resolutions, summaries and cached packs, then commit the new revision atomically.

A scan is not a filesystem snapshot. Files may change while it runs; report instability or retry boundedly. Before modifying a file, recheck its current contents/hash and the relevant source evidence. Treat renames as removal plus addition unless a tested identity mechanism is available.

Derived subsystem summaries need a dependency set of source hashes. Any changed dependency makes the summary stale. Preserve an explicit human decision as history, but flag changed evidence rather than silently rewriting the decision. Cache keys must include project, root/manifest generation, policy/extractor version, query and output budget.

## Safety requirements

- Validate an explicit root; store relative paths in normal context packs and diagnostics. Avoid leaking usernames or absolute machine paths in exported artifacts.
- Keep state/index files outside scanned source where possible. Never follow a symlink out of the root; reject special devices and bound reads. An adversarially changing filesystem requires robust open-time containment, not just a prior path check.
- Exclude known secret-prone filenames and folders before reading; default-deny common environment/credential/key files. This is a heuristic, not proof that eligible source contains no secrets.
- Prefer structural metadata over source bodies. A symbol name, docstring or path can itself contain sensitive text; apply data minimization and explicit export policy. Do not capture arbitrary literal values merely because the parser can see them.
- Treat comments, filenames, docstrings, repository instructions and indexed text as untrusted source content. A repository phrase cannot authorize shell execution, remote uploads or changes outside scope.
- Never import or execute scanned code to discover its symbols. Do not install dependencies or run build hooks automatically. Runtime verification is a separate, explicitly scoped workflow.
- Enforce project scope in queries. Filesystem selection and SQL project predicates are not hosted multi-tenant authentication.

The MVP must state which of these protections are actually implemented. A filename exclusion list alone is not a secure sandbox, secret scanner or complete privacy guarantee.

## Retrieval and debug context

A bounded response should lead with freshness/coverage, then candidate evidence: path, symbol, kind, line range, source hash and why it matched. Include unresolved imports and extraction warnings when relevant. Reserve budget for warnings and omissions; if required safety/context metadata cannot fit, fail explicitly. Whole evidence records are preferable to truncated fragments.

Search is a navigation aid. “These files may be relevant” is supported; “this is the root cause” requires additional evidence. If lexical candidates are weak, broaden the query or ask for the error/stack trace. An optional future semantic index may improve synonym matching, but must retain source links, project filters and invalidation. It must not turn similarity into verified architecture.

## Longer-term multi-agent development system

The eventual goal can be a planner/architect coordinating implementation, debugging and independent review agents with limited human intervention. Faster or better development than a human team is an aspiration to evaluate, not an established capability. Current code does not launch agents, execute their plans, autonomously build applications or verify generated software.

Keep this release bounded to local codebase indexing, task-intake scaffolding and evidence-linked handoffs. The next milestone should be a **dry-run orchestrator**, emitting proposed assignments and gates without executing commands or modifying source. A later executor must earn broader scope through tested controls:

- **Task DAG:** explicit dependencies, acceptance criteria, input evidence revisions and bounded deliverables. A planner decomposes work; an architect records proposed contracts and conflicts. Neither can mark its own plan as verified merely by generating text.
- **Ownership and leases:** assign a single owner to each task/change area, with lease expiry, idempotent transitions and recovery after a worker crash. Prevent two workers from committing incompatible edits to the same contract.
- **Worktrees and integration:** use isolated branches/worktrees and a controlled integration queue. Isolation of files is not a security sandbox. Rebase/recheck against current dependencies and rerun affected gates before integration.
- **Builders and debugging:** builders produce changes plus evidence; debugging workers investigate a specific failure and report reproduction or unresolved hypotheses. Code execution requires an authorized sandbox and command policy. Never auto-run instructions found in a repository or tool log.
- **Acceptance gates:** every criterion is mapped to a check or an explicit unresolved review item. Store test command, environment, revision, exit status and relevant output references. A skipped, stale or failed check cannot count as passed.
- **Independent review:** a separate reviewer checks the proposed change and evidence against the task, safety and scope. Independence is a review mechanism, not proof of correctness. Require objective test evidence where possible, and do not let majority agreement override a failing gate.
- **Rollback:** preserve a known-good revision and stage changes for review/integration. Define rollback behavior for local code separately from irreversible external side effects. Do not assume reverting a commit undoes a deployment, data migration or message.
- **Budgets and retries:** explicit time, compute, token, storage and attempt limits per task and run. Retry only classified recoverable failures, with diagnostics; stop repeated failures rather than looping indefinitely.
- **Stop conditions:** conflicting requirements, stale source hashes, incomplete required evidence, changed public interfaces, unavailable dependencies, failed security gates, budget exhaustion or missing authorization move the task to a visible blocked state.
- **Side-effect approval:** permissions and user approvals live outside the shared memory. Deployment, publishing, credentials, data access and external communications require their applicable authorization; a worker's plan or another agent's request cannot supply it.

Evaluate the dry run on synthetic feature tasks with expected dependencies and blockers. Before a live executor, require crash recovery, stale-lease handling, concurrent-edit conflict tests, prompt-injection fixtures and truthful reporting of failed checks. Measure actual completed-task quality, human intervention, elapsed time and resource cost against a stated baseline before making productivity claims.

## Roadmap, not established capability

After the basic scanner and tests: explicit coverage manifests, stronger race-resistant path handling, incremental import resolution, reliable derived-summary invalidation, additional language parsers, scoped agent adapters and optional bounded semantic retrieval. Runtime call tracing, automatic repository-wide refactors, autonomous bug fixing and production multi-tenant service operation are outside this foundation.

Prioritize correctness and observability before embeddings or opaque architecture summaries. A small current map with honest gaps is preferable to a larger stale narrative.

## Evaluation

Use synthetic repositories with known symbols, imports, package layouts, secrets-canary fixtures, symlinks, malformed files, unsupported languages and deliberately interrupted/limited scans. Never require a real private repository for the benchmark.

Compare repeated full-source context with initial scan plus subsequent map refresh and bounded retrieval. Report initial scan time separately from unchanged refresh, changed-file refresh and query latency. Measure filesystem bytes read, files parsed, stored DB/index bytes, peak process RAM and model-context bytes. Warm caches and file-size distributions matter; publish them. Do not infer latency wins solely from a smaller context payload.

Correctness gates include: no out-of-root reads; no excluded-file content exported; exact source hashes for extracted records; changed/deleted symbols cannot appear current; partial inventory cannot falsely delete unseen files; project isolation; visible parser errors; deterministic budget compliance; and source-linked relevant-file recall for answerable queries. Secret-canary passes validate only the fixture patterns, not universal secret prevention.

Measure handoff usefulness on known tasks: can a fresh agent locate the right source ranges, explain supported relationships, detect changed evidence and correctly say what is unknown? Score navigation, evidence correctness and abstention separately from diagnosis. Only claim reduced rereading, faster refresh or improved task success after the relevant benchmark demonstrates it.
