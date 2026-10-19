# Task-plan test selection correction

Apply over the current baseline, optional-index, legacy-codebase and workflow patches.

Fixes generic test selection that previously favored CI YAML/conftest before directly relevant filenames. Candidate ranking now prioritizes declared test filenames and test_<symbol>.py under test directories, then matching test symbols, module-related tests, generic tests and finally support/CI/docs. This remains a heuristic; it does not establish test coverage or behavior.

Every plan now requires human review and explicitly marks test relevance unverified. Candidate sources are still safely reopened and SHA-256 checked. Stale candidates are omitted with warnings. Test snippets can shorten at whole-line boundaries under the same strict character budget, retaining accurate line spans and incomplete-symbol metadata. Ordinary queries retain their prior whole-excerpt omission behavior. No tests or code execute through task planning.

Validation: 67 main tests and 4 experiment tests pass. Four new synthetic Click-shaped regressions cover symbol/filename ranking, stale-test rejection, line-preserving budget reduction and mandatory review flags. Independent code review found no blocker. A separate integration run on Click commit 2247b35ea1c47c727d7a06e51fa280e12a863ff6 confirmed tests/test_utils/test_format_filename.py ranks first for the query src/click/utils.py format_filename; source freshness and original-checkout checks also passed. The real repository is not vendored in this patch.

Token counts remain unmeasured. This fix does not add natural-language retrieval, semantic code understanding or verified test selection.
