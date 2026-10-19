"""Independent R1-R6/A1-A18 checks. Run with candidate src on PYTHONPATH."""
import importlib.util
import inspect
import itertools
import json
import os
from pathlib import Path
import random
import sys
import unittest

import click

BASELINE = Path(os.environ['CLICK_BASELINE_ROOT']).resolve()
spec = importlib.util.spec_from_file_location('_review_baseline_click', BASELINE / 'src/click/__init__.py', submodule_search_locations=[str(BASELINE / 'src/click')])
baseline = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = baseline
spec.loader.exec_module(baseline)

class PathString:
    def __init__(self, value): self.value = value
    def __fspath__(self): return self.value

class UntouchedPath:
    def __init__(self): self.calls = 0
    def __fspath__(self):
        self.calls += 1
        raise RuntimeError('Filename conversion reached')

class IntegerSubclass(int): pass


def oracle(s, n):
    if n is None or len(s) <= n: return s
    extension = os.path.splitext(s)[1]
    reserve = len(extension) + 1
    if extension and n > reserve:
        return s[:len(s)-len(extension)][:n-reserve] + '\u2026' + extension
    return s[:n-1] + '\u2026'


def outcome(fn, *args, **kwargs):
    try: return ('value', fn(*args, **kwargs))
    except Exception as error: return ('error', type(error).__name__, str(error))


class IndependentFeatureTests(unittest.TestCase):
    def test_exact_A2_through_A9_A13_through_A18(self):
        vectors = [
            ('longfilename.txt', False, 12, 'longfil….txt'),
            ('archive.tar.gz', False, 10, 'archiv….gz'),
            ('.bashrc', False, 5, '.bas…'), ('abcdef.', False, 4, 'ab….'),
            ('abc.txt', False, 5, 'abc.…'), ('abc.txt', False, 6, 'a….txt'),
            ('abc.txt', False, 1, '…'), ('', False, 1, ''), ('abc', False, 3, 'abc'),
            ('😀😀😀.txt', False, 6, '😀….txt'), ('e\u0301xyz', False, 2, 'e…'),
            ('..bashrc', False, 5, '..ba…'), ('archive.tar.gz', False, 14, 'archive.tar.gz'),
            ('abc.txt', False, 7, 'abc.txt'), ('👩\u200d💻abc', False, 3, '👩\u200d…'),
            (b'longfilename.txt', False, 12, 'longfil….txt'), ('short.txt', False, 10**10000, 'short.txt'),
        ]
        if os.name == 'posix':
            vectors.extend([
                ('/tmp/longfilename.txt', True, 12, 'longfil….txt'),
                ('/tmp/longfilename.txt', False, 12, '/tmp/lo….txt'),
                ('/dir.with.dot/abcdef', False, 8, '/dir.wi…'),
                ('/tmp/abcdef/', True, 3, ''), ('/tmp/abcdef/', False, 5, '/tmp…'),
            ])
        for index, (value, shorten, limit, expected) in enumerate(vectors):
            with self.subTest(vector=index):
                self.assertEqual(click.format_filename(value, shorten, max_length=limit), expected)

    def test_A1_default_none_compatibility_including_exceptions(self):
        inputs = ['', 'abc.txt', '/tmp/a/', '.', '..', 'a\x00b', 'a\n\x1b[31m',
                  'x\udcff.txt', '\ud800', '\udc00', b'/tmp/\xffname.txt',
                  Path('/tmp/report.txt'), PathString('/tmp/report.txt'), PathString(b'/tmp/\xff.txt'),
                  None, 10, [], object(), PathString(42)]
        for i, value in enumerate(inputs):
            for shorten in (False, True):
                expected = outcome(baseline.format_filename, value, shorten)
                with self.subTest(input=i, shorten=shorten):
                    self.assertEqual(outcome(click.format_filename, value, shorten), expected)
                    self.assertEqual(outcome(click.format_filename, value, shorten, max_length=None), expected)

    def test_A10_validation_precedes_filename_conversion(self):
        for value in (True, False, 1.0, '5', [], {}, complex(2), object()):
            spy = UntouchedPath()
            with self.subTest(type=type(value).__name__):
                with self.assertRaisesRegex(TypeError, '^max_length must be an integer or None$'):
                    click.format_filename(spy, max_length=value)
                self.assertEqual(spy.calls, 0)
        for value in (0, -1, -10**100, IntegerSubclass(0)):
            spy = UntouchedPath()
            with self.assertRaisesRegex(ValueError, '^max_length must be at least 1$'):
                click.format_filename(spy, max_length=value)
            self.assertEqual(spy.calls, 0)

    def test_valid_limit_preserves_filename_failure(self):
        spy = UntouchedPath()
        with self.assertRaisesRegex(RuntimeError, 'Filename conversion reached'):
            click.format_filename(spy, max_length=3)
        self.assertEqual(spy.calls, 1)
        for value in (None, 10, [], PathString(42), '\ud800'):
            self.assertEqual(outcome(click.format_filename, value, max_length=3), outcome(baseline.format_filename, value))

    def test_A11_input_conversion_precedes_compaction(self):
        inputs = [b'longfilename.txt', b'/tmp/\xfflongname.txt', 'x\udcfflongname.txt',
                  Path('/tmp/longfilename.txt'), PathString('/tmp/longfilename.txt'), PathString(b'/tmp/\xfflongname.txt')]
        for value in inputs:
            for shorten in (False, True):
                sanitized = baseline.format_filename(value, shorten)
                for limit in range(1, 18):
                    with self.subTest(input=repr(value), shorten=shorten, limit=limit):
                        self.assertEqual(click.format_filename(value, shorten, max_length=limit), oracle(sanitized, limit))

    def test_A12_keyword_only_and_int_subclass(self):
        sig = inspect.signature(click.format_filename)
        self.assertEqual(sig.parameters['max_length'].kind, inspect.Parameter.KEYWORD_ONLY)
        self.assertIsNone(sig.parameters['max_length'].default)
        with self.assertRaises(TypeError): click.format_filename('abc', False, 3)
        self.assertEqual(click.format_filename('abcdef.txt', max_length=IntegerSubclass(7)), 'ab….txt')
        self.assertEqual(click.format_filename('/tmp/abc', True), baseline.format_filename('/tmp/abc', True))

    def test_deterministic_corpus_invariants(self):
        rng = random.Random(58173)
        alphabet = ['a', 'b', '.', '/', '\\', 'é', '😀', '\u0301', '\u200d', '\x1b', '\n', '\udcff']
        corpus = [''.join(rng.choice(alphabet) for _ in range(rng.randrange(0, 35))) for _ in range(400)]
        corpus += ['a.tar.gz', '.bashrc', '..name', '...', 'abc.', '/dir.with.dot/file', '\\server\\share\\file.txt']
        for value in corpus:
            for shorten in (False, True):
                sanitized = baseline.format_filename(value, shorten)
                self.assertEqual(click.format_filename(value, shorten), sanitized)
                for limit in (1, 2, 3, 4, 5, 6, 8, 12, 32, 100):
                    actual = click.format_filename(value, shorten, max_length=limit)
                    self.assertEqual(actual, oracle(sanitized, limit), (repr(value), shorten, limit))
                    self.assertLessEqual(len(actual), limit)


if __name__ == '__main__':
    print(json.dumps({'candidate_import': click.__file__, 'baseline_import': baseline.__file__, 'python': sys.version, 'platform': sys.platform, 'filesystem_encoding': sys.getfilesystemencoding()}), flush=True)
    unittest.main(verbosity=2)
