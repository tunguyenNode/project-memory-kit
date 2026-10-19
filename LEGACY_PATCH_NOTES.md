# Read-only legacy-codebase onboarding patch

Apply over v0.1 plus the reviewed optional-index experiment overlay. Adds scan/update/query/handoff/task-plan CLI, a bounded read-only POSIX source scanner, incremental manifest, AST structural metadata, fresh source-linked excerpts and explicit feature/debug planning scaffold. No scanned code is imported/executed.

Safety review fixes: streamed descriptor traversal counts directories; total reads respect remaining budget; optional project-decision DB opens read-only without schema changes; deletion checks read metadata only; empty excerpts have explicit null line ranges. 46 main tests and 4 experiment tests pass. Eight original scanner tests, three independent safety regressions and one additional empty-source/credential-filename test are included.

Only synthetic repositories were scanned. No source database, manifest containing user paths, or user repository content is included. The reusable demo creates and removes a synthetic 1,001-file project. Demo timings are one local run, not performance guarantees. Token counts remain unmeasured. Generated manifests/docs/excerpts from a real repository must remain private unless their sharing is explicitly approved.

Run from project root:

    PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v
    PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s experiments -p 'test_*.py' -v
    PYTHONDONTWRITEBYTECODE=1 python examples/codebase_demo.py

See README.md for the implemented CLI, restrictions and limits; docs/codebase-harness-design.md separates implemented behavior from future orchestrator design.
