# Requirement-to-test matrix

All tests below are in `click/tests/test_utils/test_format_filename.py`, class `TestCompactFilename`. Tests use stdlib unittest and are also collectable by pytest. Each method uses deterministic subcases; the method count is not an assertion/case count.

| Acceptance | Test method(s) | Result on Linux/Python 3.12 |
| --- | --- | --- |
| A1 defaults/None/error parity | test_baseline_and_converted_inputs; test_original_regression | Pass, representative supported/invalid corpus; not exhaustive downstream proof |
| A2 unchanged short names | test_exact_vectors; test_deterministic_invariants | Pass |
| A3 extension retention | test_exact_vectors | Pass |
| A4 final suffix only | test_exact_vectors | Pass |
| A5 dotfile/trailing dot | test_exact_vectors | Pass |
| A6 extension capacity and N=1 | test_exact_vectors | Pass |
| A7 empty/equal length | test_exact_vectors | Pass |
| A8 shorten versus full path | test_native_paths | Pass on POSIX |
| A9 emoji/combining code points | test_exact_vectors | Pass |
| A10 types, bounds, access ordering | test_validation_before_filename_access | Pass, both shorten modes |
| A11 bytes/PathLike/surrogate conversions | test_baseline_and_converted_inputs | Pass |
| A12 keyword-only/int subclasses | test_signature_and_integer_limits | Pass |
| A13 dotted directories | test_native_paths | Pass on POSIX |
| A14 trailing separator | test_native_paths; test_baseline_and_converted_inputs | Pass on POSIX |
| A15 double-dot/equal limits | test_exact_vectors | Pass |
| A16 split ZWJ, N=1 | test_exact_vectors; test_deterministic_invariants | Pass |
| A17 bytes/malformed inputs | test_exact_vectors; test_baseline_and_converted_inputs | Pass using active filesystem encoding |
| A18 arbitrarily large integer | test_signature_and_integer_limits | Pass with 10**10000 |
| R3–R6 general invariants | test_deterministic_invariants | Pass, Unicode/control/path/suffix corpus |
| Native Windows drive/UNC | test_windows_drive_and_unc | Skipped; requires Windows |

The independent review has a separate script and actual pinned-package parity oracle; consult its report and logs for its counts and limits. No test result here implies the full upstream suite, Windows execution, typing, Sphinx, performance, product demand or release approval.
