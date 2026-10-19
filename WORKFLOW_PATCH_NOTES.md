# Dry-run checkpoint workflow patch

Apply over the existing baseline, optional-index and legacy-codebase patches. Adds versioned requirement scope/acceptance criteria/evidence IDs, exact-hash approval, cycle-checked worker specifications, caller-provided result records, unverified candidate issues, explicit review and acceptance gates. No agents, commands, repository code or tests execute through this engine.

Requirements edits invalidate approvals and downstream results. Replacing upstream results invalidates dependent results and review. Acceptance requires a complete submitted result set, caller-reported passing tests with evidence references, explicit review and matching hashes. Actor identities, source references and reported test outcomes are not independently verified. Accepted means a caller attestation was recorded, not that delivery occurred.

Independent safety review passed after fixing oversized-create writes, rejected-edit in-memory mutation, invalid top-level JSON handling and stale-loaded-state overwrites. Failed saves restore the prior persisted in-memory snapshot. Optimistic stale checks are not concurrent compare-and-swap locking; use one writer. Local owner-editable JSON is not a secure permission/audit boundary.

Verification: 63 main tests and 4 experiment tests pass. The synthetic workflow demo intentionally records not_run and confirms acceptance stays blocked. No real project results, user history or credentials are included.

Selected third-party skill texts are uninstalled references, pinned to commit 3cca18b368ae95cdbdebbff572ccafa662551015. Their local SHA256SUMS were verified. Their MIT license is retained; root LICENSE expressly excludes that third-party material from the project's rights-reserved notice. No runtime skills were enabled and not all transitive references are included.

Run:

    PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v
    PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s experiments -p 'test_*.py' -v
    PYTHONDONTWRITEBYTECODE=1 python examples/workflow_demo.py

Source-tree hashes, authenticated approvals, source-drift rejection, verified test capture, real worker dispatch and release gates remain future host-integrated work.
