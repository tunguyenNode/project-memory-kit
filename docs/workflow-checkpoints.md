# Checkpointed codebase delivery workflow

## Scope and implementation boundary

The intended experience is a development partner that maps a legacy codebase, prepares missing documentation, reports evidence-backed issues, clarifies a new task, and coordinates implementation after the user freezes requirements. User checkpoints remain explicit even if routine work between checkpoints eventually becomes automated.

**Current MVP:** a local scanner extracts limited structural evidence; bounded query and task-plan commands assemble source-linked context and caller-supplied criteria. It does not perform LLM codebase understanding, independently discover verified bugs, generate validated architecture documentation, launch agents, write feature code or execute tests. Generated structural handoffs are not comprehensive developer documentation. Every issue example in this document is a template, not a finding about any real repository.

**Implemented local dry-run checkpoint engine:** `project_memory/workflow.py` exposes `create`, `edit`, `show`, `submit`, `approve`, `plan`, `result`, `review` and `accept` through `python -m project_memory.workflow COMMAND FILE`. It records caller-supplied planning and result attestations; it does not start workers or perform the work described in them. Its single-writer JSON file is locally editable and is not authenticated, tamper-proof or an access-control boundary. Actor names, logs, evidence references, test outcomes and acceptance are caller claims, not machine-verified identity or execution.

Implemented sequence: `draft` → `awaiting_requirements` → `approved` → `planned` → `awaiting_review` → `awaiting_acceptance` → `accepted`. Here `accepted` means an explicit caller acceptance attestation was recorded, not that this program built, tested or delivered software. Requirement edits reset approvals, DAG and results; changed upstream results invalidate dependent results and review. Rejected review returns to planning. The implementation is a smaller checkpoint mechanism than the complete target workflow below.

- `create`/`edit` take repeated scope, criterion and evidence values.
- `approve` requires the exact requirement `--hash` and an `--actor` label.
- `plan` validates a DAG; its default roles are architect → implementer → tester → reviewer. No agents are launched.
- `result --record-json` ingests output summaries/references, evidence, test outcomes/logs and candidate issues. These are marked as unverified caller submissions; issues remain candidates.
- `review` binds the requirement hash and exact `--results-hash` to an actor label, decision and notes. Passing-test and review prerequisites are checks on submitted data, not independent verification.
- `accept` requires exact current hashes and explicit acceptance. It does not deploy or execute anything.

The live execution system remains future work. The current engine does not execute code, modify source, install dependencies, contact services or deploy. Select a dedicated output state file outside the source tree; the broader root-containment and trusted-host requirements below are design requirements, not guarantees supplied by an editable JSON checkpoint file.

## Target full-workflow state machine

For the target production workflow, every state change should record workflow ID, prior state, event ID, actor identity supplied by the trusted host, timestamp, plan version/hash and evidence references. Duplicate event IDs are idempotent. Out-of-order transitions fail with a reason. The orchestrator cannot turn a retrieved statement into an approval.

| State | Required evidence or action | Next state |
|---|---|---|
| `NEW` | User task and explicit repository/project selection | `DISCOVERY_PENDING` |
| `DISCOVERY_PENDING` | Inventory/coverage snapshot and sourced observations | `DISCOVERY_REVIEW` |
| `DISCOVERY_REVIEW` | Coverage, unknowns and documentation/issue candidates presented; user selects scope or asks for more investigation | `REQUIREMENTS_OPEN` or `DISCOVERY_PENDING` |
| `REQUIREMENTS_OPEN` | Blocking questions answered; scope, non-goals and testable acceptance criteria drafted | `PLAN_REVIEW` |
| `PLAN_REVIEW` | Exact versioned plan shown to user | `PLAN_APPROVED`, `REQUIREMENTS_OPEN`, or `CANCELLED` |
| `PLAN_APPROVED` | Trusted host supplies explicit user approval bound to exact plan hash/version | `READY_FOR_HANDOFF` |
| `READY_FOR_HANDOFF` | Validated DAG, worker contracts, budgets and required permissions | `DRY_RUN_COMPLETE` in this milestone; `IMPLEMENTING` only in a future authorized executor |
| `IMPLEMENTING` | Future workers produce scoped patches and attributable evidence | `VERIFICATION_PENDING` |
| `VERIFICATION_PENDING` | Required checks and independent review assessed against acceptance criteria | `ACCEPTANCE_REVIEW` or `REWORK_REQUIRED` |
| `REWORK_REQUIRED` | Failure classified; bounded in-scope retry allowed, otherwise revised plan | `IMPLEMENTING` or `PLAN_REVIEW` |
| `ACCEPTANCE_REVIEW` | User receives delivered revision, criterion outcomes, review findings and remaining risks | `ACCEPTED`, `REWORK_REQUIRED`, or `CANCELLED` |
| `ACCEPTED` | User accepts delivered result; deployment remains a separate decision | `DEPLOYMENT_REVIEW` if deployment requested, otherwise terminal |
| `DEPLOYMENT_REVIEW` | Specific target, version, side effects, rollback and required approvals reviewed | `DEPLOYMENT_AUTHORIZED` or `ACCEPTED` |
| `DEPLOYMENT_AUTHORIZED` | Future executor has independently valid action permissions | `DEPLOYED` only with actual deployment evidence |

In an execution preview, the target workflow stops at `DRY_RUN_COMPLETE` and shows later execution stages as `not_started`. The implemented local checkpoint engine additionally records caller-supplied results/review/acceptance for rehearsal or externally performed work. Those attestations must never be displayed as evidence that this engine executed or independently verified anything. No deployment state exists in the current engine.

`BLOCKED` and `CANCELLED` are available from any nonterminal state. `BLOCKED` stores a reason, missing evidence/permission, owner and resumable prior state. A resumed workflow must revalidate the plan and source versions. Silence and elapsed time do not approve a checkpoint.

## Checkpoint 1: discovery and documentation

Discovery must say what was inspected and what remains unknown. A syntax map supports navigation; it does not prove runtime behavior. Source claims need file paths, content hashes and spans, and runtime claims need actual separate execution evidence.

Use this discovery report template:

```yaml
workflow_id: example-only
repository_identity: supplied-by-host
manifest_revision: hash-of-manifest
coverage:
  policy: selection-and-exclusion-policy-version
  complete_under_policy: false
  indexed_files: 0
  skipped_and_errors: []
  unsupported_languages: []
  uninspected_areas: []
observed_structure: [] # claim + evidence_refs + extraction/observation method
architecture_hypotheses: [] # clearly unverified, with proposed verification
unknowns: [] # question, consequence, proposed next inspection
missing_documentation: [] # audience, proposed artifact, evidence needed
issue_candidates: [] # IDs from issue template below
user_decisions_needed: []
```

Useful documentation deliverables include an entry-point map, subsystem responsibilities, setup instructions, data flows, testing guide and current handoff. Generate each only to the extent supported by evidence. Setup commands inferred from files are `suggested_unverified` until tested in an authorized environment. Do not fabricate endpoints, dependencies, environmental requirements or successful setup steps.

Issue template:

```yaml
issue_id: candidate-001
status: hypothesis # hypothesis | supported_static_finding | reproduced | dismissed
summary: caller-or-reviewer-supplied-description
source_evidence: [] # path, hash, span, observation
expected_behavior: unknown # include source of expectation when known
observed_behavior: not_executed
impact: unknown
severity_basis: unknown # no precise severity without justified impact
reproduction: not_attempted
confidence_basis: static_evidence_only # categorical basis, not invented probability
alternative_explanations: []
proposed_implementation: [] # candidate changes, not applied changes
proposed_verification: []
risks_and_dependencies: []
user_scope_decision: pending
```

A static suspicion is not a reproduced bug. An issue report should make the next verification step concrete without inventing results.

## Checkpoint 2: requirements freeze

The user should approve a plan that is specific enough to reject scope drift. Resolve blockers first; keep optional questions visibly deferred. Do not claim inferred preferences as confirmed requirements.

```yaml
plan_id: plan-001
version: 1
plan_hash: computed-over-canonical-plan
source_manifest_revision: required
task: explicit-user-request
blocking_questions: []
answers: [] # question ID, answer, source/actor
scope: []
non_goals: []
constraints: [] # compatibility, data, security, resource and permission constraints
assumptions: [] # each marked confirmed or unconfirmed
acceptance_criteria:
  - id: AC-1
    statement: caller-provided-testable-outcome
    verification_method: proposed-check
    evidence_required: proposed-output
proposed_changes: [] # paths/interfaces and rationale, not committed changes
required_checks: []
risks_and_rollback: []
budgets: {max_attempts: 2, max_elapsed_seconds: 1800} # illustrative, caller config wins
external_side_effects: []
open_items: []
```

The approval prompt must identify the plan version, scope, acceptance criteria and material side effects. Approval binds to the exact canonical plan hash; an approval from a prior version is not reusable for a changed plan. The trusted host verifies the authenticated user and records the approval reference. Do not accept arbitrary `approved: true` in a repository file, model response or worker message.

New scope, changed acceptance criteria, consequential interface changes, newly required permissions or new external side effects return the workflow to `PLAN_REVIEW`. Ordinary in-scope implementation detail can remain delegated if the approved plan allows it. Changed source evidence forces impact review; if approved commitments change, obtain renewed approval.

## Checkpoint 3: worker contracts and DAG

Validate unique task IDs, an acyclic dependency graph and explicit criterion coverage. Every required acceptance criterion needs an owner and verification step. No task may depend on a nonexistent task or consume stale evidence silently.

```yaml
worker_contract:
  task_id: implement-001
  role: builder # planner | architect | builder | debugger | reviewer
  plan_hash: required
  depends_on: []
  owned_paths: []
  read_scope: []
  evidence_refs: []
  deliverable: proposed-patch-and-explanation
  acceptance_ids: [AC-1]
  allowed_actions: [] # dry run: no execution actions
  prohibited_actions: [deploy, publish, upload, install]
  budget: {max_attempts: 2, max_elapsed_seconds: 600}
  stop_conditions: [stale_evidence, scope_conflict, missing_permission]
  verification_contract: proposed-checks-only
  lease: null # future executor responsibility
```

Future workers need bounded leases, isolated worktrees, conflict-aware integration and recovery after crashes. A reviewer must assess the produced artifact independently against the approved plan; it cannot approve a new requirement on the user's behalf. A worker's completion message is a claim until backed by the required artifact and verification evidence.

## Checkpoint 4: verification and user acceptance

For a future executor, preserve the distinction between `not_run`, `running`, `passed`, `failed`, `blocked` and `skipped`. A proposed test command, existing test filename or generated test file is not a successful test result.

```yaml
delivery_report:
  plan_hash: required
  delivered_revision: required-for-real-delivery
  changed_paths: []
  acceptance_results:
    - criterion_id: AC-1
      status: not_run
      evidence_refs: []
  checks: [] # command, environment, revision, timestamps, exit status, output refs
  review: {status: not_started, reviewer: null, findings: []}
  known_limitations: []
  rollback: not_verified
  user_acceptance: pending
  deployment: not_requested
```

Require checks against the delivered revision and relevant environment. Changing code after a pass invalidates the affected check result until rerun. Unresolved blocking findings prevent acceptance-ready status. Expose residual risks; do not quietly convert failed criteria into non-goals. The user may reject or request rework without approving deployment.

Deployment is a separate gate with exact destination/version, migration/data consequences, rollback limits and applicable permissions. Acceptance of source code does not authorize production deployment, publishing, spending or communications.

## Proposed host-integrated API

The following trusted-host API is a further specification, not the current Python/CLI interface. The local engine above implements a subset of the checkpoint concepts without authenticated host approvals:

```text
create_workflow(task, repository_identity, output_directory, limits) -> workflow_id
attach_discovery(workflow_id, report, evidence_manifest_hash) -> DISCOVERY_REVIEW
draft_plan(workflow_id, requirements, criteria, questions, dag) -> plan_version_and_hash
record_approval(workflow_id, plan_hash, trusted_host_approval_reference) -> PLAN_APPROVED
validate_handoff(workflow_id, current_manifest_hash) -> validation_report
emit_dry_run(workflow_id, plan_hash) -> contracts_and_checkpoint_report
revise_plan(workflow_id, changes) -> new_version_in_PLAN_REVIEW
block(workflow_id, reason, missing_evidence_or_permission) -> BLOCKED
cancel(workflow_id, trusted_host_user_reference) -> CANCELLED
```

`record_approval` is an adapter boundary, not an authentication implementation. If the host cannot verify the user approval, leave `PLAN_REVIEW` pending. Dry-run output must say `execution_performed=false`, `tests_run=false`, `agents_launched=false` and `deployment_performed=false`. A proposal can describe eventual commands but must not expose a shell execution path.

Store immutable plan versions and append-only transition records, with atomic state updates and caller-scoped access checks. Validate incoming report structure and size. Recompute plan hashes locally. Evidence content remains untrusted and must not be concatenated into privileged instructions. Do not include private source excerpts in telemetry or public examples.

## Authority, stop rules and acceptance tests

Skills, repository instructions, comments, memory and worker outputs can be reference material. They cannot grant user approval, waive a checkpoint, expand tool permissions or override the host's policy. Model-generated approvals and self-awarded review passes are invalid.

Stop on stale required evidence, unresolved contradictions, missing authorization, unsupported required analysis, exhausted budgets or repeated failures. State the smallest missing decision or evidence needed to resume. Never compensate by claiming success or silently broadening access.

Before claiming the full target orchestrator or a trusted execution boundary, test: stale-plan approval rejection; authenticated approval boundary; duplicate event idempotency; DAG cycles/missing dependencies; acceptance criteria without verification; changes after approval; malformed/oversized reports; partial scan coverage; false worker completion; prompt-injection text in evidence; cancellation; restart recovery; and rejection of execution/deployment events in dry-run mode. Assert that source trees are unchanged and no worker, shell, network or deployment actions occur.

Success for a host-integrated checkpoint milestone means a user can inspect a concrete plan and deterministic proposed handoff, approve the exact version, and see truthful pending statuses. It does not mean an application was built or a legacy system was fully understood.
