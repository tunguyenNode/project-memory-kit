# Click compact filename display: local demo requirements v1

## Status and authority
Proposed demonstration feature, selected by dot under the user's delegated demo authority ("bạn hãy tự chốt hoặc làm việc với antigravity"). This is not an upstream-approved Click roadmap item, release decision, or permission to publish an issue/PR. No feature implementation is included. Requirements status: READY FOR LOCAL IMPLEMENTATION subject to the independent review verdict recorded separately. This is not a claim of implemented or tested code. Existing repository behavior is evidence; all new product rules below are agent-authored decisions, not automatically discovered requirements.

## Business goal, people, value
CLI authors building narrow progress/status views need bounded display labels without changing actual file paths. Operators benefit from shorter labels and a recognizable final extension. The value hypothesis is less horizontal clutter, not guaranteed unique identification or exact terminal-column fit. No user research or demand validation was performed. Success for this demo: deterministic bounded strings, explicit opt-in, and zero changes to default calls.

## Scope and API
Extend existing public format_filename(filename, shorten=False, *, max_length=None) -> str. max_length: int | None. No new public function/export. Existing positional filename and shorten calls stay valid. A third positional argument is rejected by the Python signature. Existing callers in types.py and exceptions.py remain unchanged; no automatic truncation of error messages. Actual filesystem paths, IO and filename validation are untouched.

## Chosen business rules
R1. Validate max_length first, before calling os.fspath or invoking an object's __fspath__. None disables the feature. Accept built-in int and int subclasses, excluding bool. Other types raise TypeError with message "max_length must be an integer or None". Integers below 1 raise ValueError with message "max_length must be at least 1". No upper limit. No numeric coercion.
R2. Run existing conversion unchanged: shorten uses host-platform os.path.basename, otherwise os.fspath; bytes decode with the filesystem encoding and replace, str follows the existing surrogateescape/replace conversion. Preserve existing failures on invalid filename inputs; do not expand the supported domain. Do not resolve paths, read the filesystem, normalize Unicode, or parse foreign-platform separators.
R3. After conversion, call the result S. If max_length is None or len(S) <= max_length, return S exactly, including empty strings. Length is Python Unicode code points. Combining marks, grapheme clusters, emoji sequences, control characters, ANSI codes and East Asian characters receive no special interpretation. Documentation must warn this is not a terminal-cell limit and may split a grapheme.
R4. If truncation is needed, determine extension E using host-platform os.path.splitext(S)[1] on the entire sanitized string. This uses the final suffix only: .tar.gz keeps .gz; a leading-dot filename such as .bashrc has no extension; a trailing dot is extension '.'. Directory dots do not become extensions. No MIME/compound-extension registry. The same host semantics used by existing basename apply.
R5. Let N = max_length and marker be the single character U+2026 ('…'). If E is nonempty and N >= len(E)+2, return the first N-len(E)-1 code points of S without its final extension, then marker, then E. This guarantees at least one prefix code point plus marker plus extension. The prefix can include directory text when shorten=False; preserving the basename is not promised.
R6. Otherwise return S[:N-1] + marker. Therefore N=1 always returns marker for a nonempty truncated name, and oversized extensions are not preserved. No suffix-only special case. Truncation is display-only and lossy; never use the result for IO or assume uniqueness. No additional redaction/security guarantee.

## User flows
1. Existing application calls format_filename(path): output remains unchanged.
2. CLI author opts into format_filename(path, shorten=True, max_length=12), then displays the returned label; original path remains the IO value.
3. CLI author keeps path context with shorten=False and max_length=12; the prefix can contain directories and extension is retained only if the capacity rule allows it.
4. Invalid configuration fails before interacting with filename objects; caller fixes it rather than receiving silent coercion.

## Non-goals
Terminal-column precision; Unicode grapheme preservation; automatic terminal width detection; changing all Click error output; path abbreviations prioritizing basename; collision avoidance; extension/MIME inference; new packages; external submissions; performance claims; production approval.

## Acceptance scenarios (Given / When / Then)
A1. Given every currently supported filename and shorten call, when max_length is omitted or None, then output and exceptions match the baseline.
A2. Given sanitized S whose length is <= N, when max_length=N, then return S unchanged, with no marker.
A3. Given S='longfilename.txt', when N=12, then output 'longfil….txt' (12 code points).
A4. Given S='archive.tar.gz', when N=10, then output 'archiv….gz'; preserve final .gz only.
A5. Given S='.bashrc', when N=5, then output '.bas…'. Given S='abcdef.', N=4, then 'ab….'.
A6. Given S='abc.txt', N=5, then '….txt' is forbidden because it lacks a prefix; expected 'abc.…'. Given N=6, expected 'a….txt'. Given N=1, expected '…'.
A7. Given an empty name, when N=1, then return ''. Given S='abc', N=3, return 'abc'.
A8. Given POSIX path '/tmp/longfilename.txt', when shorten=True and N=12, then 'longfil….txt'; when shorten=False, then '/tmp/lo….txt'. Equivalent host-native separator cases run on Windows.
A9. Given S='😀😀😀.txt', N=6, then '😀….txt', regardless of actual rendered width. Given S='e\u0301xyz', N=2, then 'e…' (no grapheme guarantee).
A10. Given invalid max_length types True, False, 1.0, '5', [], when called, then exact R1 TypeError. Given 0 or -1, then exact R1 ValueError. Filename objects are not touched in those cases.
A11. Given bytes, PathLike[str], PathLike[bytes], or a supported surrogateescaped filename, when compacting, then conversion occurs before length and extension calculation; compare sanitized baseline S against R3–R6.
A12. Given a third positional argument, when called, then Python raises TypeError; existing two-position calls remain valid. int subclass values are accepted.

## Test matrix and implementation work
No tests of this new feature have run. The existing maintenance exercise tests a different, pre-existing behavior.
- Parameterized exact vectors A2–A9: tests/test_utils/test_format_filename.py.
- Validation, order, int-subclass, positional and input-type coverage A10–A12 in the same test module. Use a spy PathLike to prove invalid limits never call __fspath__.
- Existing baseline tests + added None parity for str/bytes/PathLike/surrogateescape/empty/trailing separators/invalid filename inputs: A1.
- Cross-platform os.path semantics: native separator paths, dotted directory, Windows drive and UNC paths on Windows. Foreign separators follow host semantics; no portable reinterpretation.
- General invariants across a deterministic varied corpus: compact output length <= N, defaults identical, unchanged short strings, extension retained exactly whenever R5 applies.
- Docs examples and type signature review. No new dependency required.

Candidate files: src/click/utils.py (signature, validation, post-conversion formatting, docstring; qualify the existing "without failing" claim for valid supported inputs/options); tests/test_utils/test_format_filename.py (tests); docs/utils.md (opt-in example, limitations, error behavior; replace the overbroad existing "will never fail" statement with a conversion claim limited to supported filename inputs and valid options). Inspect docs/api.md and src/click/__init__.py but no changes expected because the function is already exposed. A changelog/release note is out of this bounded local demo; release owners decide separately.

Dependency DAG:
T1 Verify pinned tree and source evidence; inspect project test instructions → T2 Review frozen rules and acceptance vectors → T3 Implement narrow utils change and docstring + T4 Write parameterized tests + T5 Update docs (T3/T4/T5 may be separate workers but share frozen rules) → T6 Run focused existing/new tests, then full supported suite if environment permits → T7 Independent diff/test/provenance review → T8 Local user acceptance checkpoint. T6 waits for T3/T4/T5. Do not invent test-pass evidence or install missing dependencies without appropriate authorization. Record exact commands, environment, revision/tree hashes, output and limitations. Replan if source drifts, required dependencies are unavailable, or implementation demands wider API change.

## Remaining uncertainty and decision checkpoints
No business decision is intentionally left open in this bounded demo: dot chose code-point counting, final-suffix policy, error contracts and opt-in scope. Independent review may identify missing rules; those block readiness until explicitly resolved. Product demand, upstream acceptance, actual performance, full dependency/caller impact and cross-platform execution are unverified, but do not block writing the bounded local implementation. No question to the user is required for these delegated demo choices. Publishing/releasing, changing all error callers, adding dependencies, or expanding scope requires a separate checkpoint.

## Harness versus agent contribution
Raw automatic outputs are harness-query.json and harness-task-plan.json. Harness found the existing function and its relevant nine-line test, hash-verified excerpts, included caller-supplied criteria, and marked needs_review/human_review_required/test_relevance_unverified. It did not invent this feature, determine personas/value, choose rules, discover complete caller impact, design these acceptance vectors or run tests. It also returned unrelated utils test candidates and omitted 56 candidates. This requirements pack, DAG and test design are agent-authored analysis. The harness alone does not supply a complete business-logic handoff; an agent can construct one using its evidence plus explicitly delegated choices and independent review.

## Source and test-command handoff
See source-evidence.json for official pinned-source links, line ranges and whole-file SHA-256. The target baseline is commit 2247b35ea1c47c727d7a06e51fa280e12a863ff6, clean when inspected. Newness means absent from this pinned API/implementation/docs, not a worldwide feature-novelty claim.

Agent-proposed commands after authorized implementation, from the copied Click root with a confirmed pytest-enabled environment: PYTHONPATH=src python -m pytest tests/test_utils/test_format_filename.py -q; then PYTHONPATH=src python -m pytest -q. These are not harness-generated or executed results. pyproject.toml declares pytest and configures default exclusion of stress-marked tests; a default suite pass must disclose that exclusion. If pytest/dependencies are missing, report not_run and request/route the necessary setup instead of substituting a misleading pass. Cross-platform verification requires actual supported Windows and POSIX runs; a POSIX-only pass cannot establish Windows execution.

## External critique resolution and additional exact cases
Antigravity suggested treating a trailing dot as no extension. dot's final delegated choice retains host os.path.splitext semantics, including '.' as the final extension, because it is a simple documented standard-library rule consistent with the rest of the feature. A5 explicitly locks that behavior. No rendered-character counts supplied by a reviewer are accepted as test evidence; these are expected code-point results to test after implementation.

Additional acceptance/test vectors (POSIX for literal slash paths):
- A13: '/dir.with.dot/abcdef', shorten=False, N=8 → '/dir.wi…'. Dots in the parent directory do not create an extension.
- A14: '/tmp/abcdef/', shorten=True, N=3 → ''; the existing basename of a trailing separator is empty. With shorten=False, N=5 → '/tmp…'.
- A15: '..bashrc', N=5 → '..ba…'; 'archive.tar.gz', N=14 → 'archive.tar.gz' unchanged; 'abc.txt', N=7 → 'abc.txt' unchanged.
- A16: S='👩\u200d💻abc', N=3 → '👩\u200d…', even though truncation splits a ZWJ sequence. This intentionally demonstrates the code-point, not grapheme, contract. N=1 on any longer valid sanitized string → '…'.
- A17: b'longfilename.txt', N=12 → 'longfil….txt'. For malformed bytes/surrogateescaped inputs, first capture baseline sanitized S under the active filesystem encoding, then assert the exact R3–R6 transformation of that S; do not hard-code an OS encoding assumption.
- A18: An arbitrarily large valid Python int leaves a short S unchanged (no overflow/upper-limit policy); length counts are evaluated before any truncation slicing.

The existing R1–R6 decide these cases without new business-rule inventions. These cases join the implementation test matrix, not claims of already-run feature tests.
