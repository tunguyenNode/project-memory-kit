# Experimental retrieval patch

Apply these files over the unchanged v0.1 baseline. This patch does not alter the default store, CLI or session harness retrieval behavior.

Adds an opt-in FTS5/zero-hit-fallback retrieval adapter, 9 optional-index tests, a four-test experiment suite, reproducible five-strategy synthetic comparisons, raw results and limitations. The complete main suite is 34 tests; the separate experiment suite is 4 tests. Independent review found no release blocker for opt-in experimental use after substring post-filtering fixed FTS normalization false positives.

No tokenizer was available, so bytes/characters are measured and token_count is null. No token-cost, universal speed or semantic-recall claim is made. Partial nonempty FTS results may omit substring-only matches; this is documented and tested. Use the original MemoryStore.search to retain default substring semantics. No private/user data or databases are included.

Run from the project root:

    PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v
    PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s experiments -p 'test_*.py' -v
    PYTHONDONTWRITEBYTECODE=1 python experiments/compare_retrieval.py

The benchmark uses temporary synthetic SQLite databases and the built-in FTS5 module only.
