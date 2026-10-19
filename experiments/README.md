# Memory organization comparison

## Decision

Keep the released v0.1 scan-based behavior unchanged. The indexed alternatives were much faster on these warm, exact-token fixtures, but they did not preserve substring recall. No architecture is declared universally best, and the human-memory analogy was not treated as an optimization rule.

The experiment is separate from the shipped harness. Nothing here calls a model, installs software, sends data, or requires an embedding service. It uses Python's built-in SQLite FTS5 if available. Missing FTS5 is reported rather than installed.

## Reproduce

From the project root:

```sh
PYTHONDONTWRITEBYTECODE=1 python experiments/compare_retrieval.py > experiments/results.json
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s experiments -p 'test_*.py' -v
```

The temporary databases contain synthetic data and are removed afterward. Runtime is roughly a couple of minutes on the test machine; it varies. The JSON contains every query's p50/p95, context bytes, selected-record count, warning check, project-boundary count and budget check. The test suite separately verifies trigger rollback and literalization of FTS operators.

## Organizations tested

1. Full history: return every project record, including superseded revisions, and pack it under the same budget without query selection.
2. Linear active: the existing MemoryStore search, which scans active records and performs all-term substring matching.
3. Event FTS: a full-text index over all events, joined back to the authoritative rows and filtered to the current project and unsuperseded records.
4. Materialized active FTS: a materialized current-record table and its own full-text index. Insert triggers update it and remove the superseded current record atomically.

All use the same record shape, 8,000-character packing envelope and evaluation-only selected-record warning function. This isolates a practical retrieval-plus-packing workflow, not the exact production session_start implementation. Production warning generation still scans all active records and also uses age-based staleness; this experiment checks selected-record explicit review dates against a fixed date.

## Corpus and expected answers

Two projects contain either 1,000 or 10,000 unrelated synthetic facts each, plus small fixed fixtures. Nine queries test an exact current decision, multiple terms, a superseded-only word, an explicitly stale fact, unresolved conflicting decisions, a foreign-project marker, no match, a paraphrase, and a substring.

The expected IDs are hand-defined by the generator. Each query runs 20 times after warm-up. A single expected-ID match is a retrieval check, not an assessment of language-model answer quality. Full history fails the exact-result criterion because it returns unrelated and superseded records; that does not mean it lacks every relevant record or proves a downstream model could not answer.

## Measured results

Python 3.12.14, SQLite version and platform are recorded in results.json. On this run:

| Records per project | Linear p50 / p95 | Event FTS p50 / p95 | Materialized FTS p50 / p95 |
|---|---:|---:|---:|
| 1000 | 2.013 / 2.072 ms | 0.029 / 0.032 ms | 0.028 / 0.032 ms |
| 10000 | 29.181 / 39.023 ms | 0.029 / 0.051 ms | 0.030 / 0.069 ms |

At both corpus sizes:

- Linear search matched the full expected ID set on 8 of 9 fixtures.
- Both FTS alternatives matched on 7 of 9 fixtures.
- All lexical approaches missed the paraphrase “relational persistence” for the SQLite decision.
- FTS additionally missed “SQL”, which substring matching found in “SQLite”. This is a real behavior change, not an improvement to hide behind a faster average.
- No strategy returned a foreign-project record. Context outputs stayed within the declared budget.
- On the exact decision query at 10,000 records, selected packs were 439 bytes, versus 7,751 bytes for the budgeted full-history pack. The latter omitted most records; size alone does not establish useful context quality.
- Indexes immediately reflected a post-build insertion and explicit supersession. Independent tests verified rollback leaves both indexes consistent.

Building both indexes together took 9.038 ms for the smaller corpus and 97.257 ms for the larger. The larger database grew from 3,842,048 to 12,427,264 bytes with both indexes and the materialized copy. This combined overhead cannot be attributed independently to either candidate. Faster lookup has a storage and maintenance cost.

## What this does and does not establish

The indexed paths can sharply improve this particular warm token-lookup workload. The materialized path did not show a consistent meaningful advantage over event FTS on the small query set, so its additional state is not justified by this test alone.

This is one deterministic corpus, fixed query order and one run with 20 warm repeats per query. It does not measure cold caches, separate-process memory/RSS, independent index storage cost, sustained writes, deletion, adversarial concurrency, semantic recall on real projects, model tokens/cost, or end-to-end agent task time. Warning behavior is narrower than the production harness. Timing differences must not be promoted into a universal speed or resource-efficiency claim.

The experiment has no deletion/update triggers because the store API is insert-and-supersede only. Direct SQL modification is outside its consistency assumptions. It is not a production migration or a security boundary.

## Next decision gate

Before adopting an index, define whether substring behavior is required. Then compare an indexed design with an explicitly measured fallback against the existing behavior on a larger held-out fixture set. Include realistic paraphrases, source changes, conflict groups, project boundaries, cold/warm runs, write/storage overhead and warnings. Require unchanged or improved retrieval correctness and isolation before accepting latency gains. A semantic layer may help paraphrases, but its accuracy and resource costs need separate evidence; it is not assumed necessary or enabled here.

## Fifth candidate and target-retrieval metrics

A separate follow-up run adds a zero-hit hybrid: query the event FTS index, filter token candidates through the original substring predicate to remove punctuation/diacritic normalization false positives, and fall back to the original scan when none remain. Partial nonempty hits can still miss other substring-only records; the optional library's regression tests demonstrate this. No baseline-default change is authorized by an 8-of-9 fixture result alone.

The final run records precision and recall against expected synthetic record IDs, source-pointer presence, exact packed-ID matches and budget compliance. For empty expected sets, recall is defined as 1; precision is 1 only for an empty result. Source-pointer presence means the caller-provided synthetic source label exists. It does not establish source authenticity, availability or truth.

Token counts are not measured. No tiktoken, transformers or tokenizers package was available in the local environment, and no external model/tokenizer API was called. Results therefore record token_count as null. Character/byte reductions are not presented as tokenizer-specific token or inference-cost reductions. Record-level selection is implemented; query-specific excerpts, source-span pointers and tokenizer-aware packing remain future work.

## Final five-strategy run

The reviewed post-filtered hybrid results are in `results-final.json`. They supersede the unfiltered exploratory hybrid run; the earlier `results.json` remains the original four-strategy comparison.

At 10,000 records per project, the exact-current-decision query measured:

| Retrieval path | p50 | p95 | Expected-ID fixtures matched |
|---|---:|---:|---:|
| Original linear scan | 27.990 ms | 34.411 ms | 8/9 |
| Event FTS | 0.034 ms | 0.126 ms | 7/9 |
| Materialized active FTS | 0.034 ms | 0.061 ms | 7/9 |
| Post-filtered zero-hit hybrid | 0.032 ms | 0.040 ms | 8/9 |

The hybrid's substring query fell back to scanning and took 25.236 ms p50. It is not always faster. Its nine-fixture ID match rate equals the baseline in this test, but the independent partial-hit unit test demonstrates that it is not generally recall-equivalent. All paths remain lexical and miss the paraphrase fixture.

All five strategies stayed within the context budget and returned zero foreign-project records. Returned records had nonempty synthetic source pointers. Those are pointer-presence checks, not evidence validation. The exact decision pack at this scale is 439 bytes; no tokenizer-specific token count was measured. Detailed precision/recall and returned/expected IDs are in the raw JSON, including the full-history baseline's low precision and budget omissions.

Decision: keep linear search as default. Make the reviewed hybrid available only as an explicit experimental retrieval API, with fallback and recall diagnostics. It does not replace Harness.session_start or bypass the host's warning, provenance, budget or permission policies.
