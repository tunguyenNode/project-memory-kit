# Click compact filename: tested feature example

This bounded example demonstrates turning explicit requirements into a narrow implementation and independently verified tests. It is not an upstream Click release, endorsement, or PR. The harness retrieves evidence and candidates; the feature rules, implementation and review were agent-authored. It does not prove the harness autonomously discovers complete business requirements.

## Use

After applying `feature.patch` to the pinned Click checkout, use:

```python
import click
original = "longfilename.txt"
label = click.format_filename(original, shorten=True, max_length=12)
assert label == "longfil….txt"
```

Keep `original` for IO. `max_length` is keyword-only; omitted or None preserves baseline conversion. Positive integers including subclasses are accepted; bool and other types raise TypeError, values below 1 raise ValueError before accessing the filename. Limits count Unicode code points, not terminal width or graphemes. The ellipsis counts toward the limit. Only the final extension survives when a prefix character and ellipsis also fit. Host `os.path` semantics apply, including trailing-dot extensions. Labels are lossy, may split emoji and need not be unique. Existing error callers are unchanged.

## Reproduce

Requires Git, Python 3.10+ with venv, and network access to official PyPI to install pytest and the declared Flit build backend. Inspect the runner before use. It works in a temporary directory without changing your original checkout.

```sh
git clone https://github.com/pallets/click.git /tmp/click-upstream
bash examples/click-compact-filename/run_checks.sh /tmp/click-upstream
```

The runner exports baseline commit `2247b35ea1c47c727d7a06e51fa280e12a863ff6`, checks/applies the patch, installs only in its isolated venv, and runs focused, independent and default full tests. It reports its retained temporary directory. The default upstream suite excludes stress tests. Windows checks require an actual Windows host; this Bash runner targets POSIX.

To check the containing memory-kit project from its root:

```sh
python -m unittest discover -s tests -v
python -m unittest discover -s experiments -p 'test_*.py' -v
```

See `ACCEPTANCE.md` and `TEST-EVIDENCE.log` for actual results. `FROZEN-REQUIREMENTS.md` is preserved verbatim as historical evidence: its original pre-implementation status and test wording describe when it was authored. No full upstream checkout is vendored. The patch contains Click-derived source/context; preserve `CLICK-LICENSE.txt` (BSD-3-Clause). `SHA256SUMS` covers this example's deliverables, excluding itself.
