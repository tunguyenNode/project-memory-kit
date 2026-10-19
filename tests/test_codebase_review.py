"""Independent scanner regressions using disposable synthetic repositories only."""
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from project_memory import codebase


class CodebaseReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.root = self.base / 'repo'
        self.root.mkdir()
        self.state = self.base / 'state'

    def tearDown(self):
        self.temp.cleanup()

    def test_empty_directories_consume_traversal_budget(self):
        for index in range(50):
            (self.root / f'directory_{index}').mkdir()
        result = codebase.scan(self.root, self.state, max_paths=1)
        self.assertFalse(result['complete'])

    def test_failed_decision_read_does_not_modify_unrelated_database(self):
        (self.root / 'app.py').write_text('def target(): pass\n')
        codebase.scan(self.root, self.state)
        database = self.base / 'unrelated.db'
        with sqlite3.connect(database) as connection:
            connection.execute('CREATE TABLE unrelated(value TEXT)')
        before = database.read_bytes()
        with self.assertRaises((ValueError, sqlite3.Error)):
            codebase.task_plan(self.root, self.state, 'Synthetic task', 'target',
                               memory_db=database, project='missing')
        self.assertEqual(database.read_bytes(), before)

    def test_growing_file_cannot_exceed_total_read_budget(self):
        source = self.root / 'app.py'
        source.write_text('#a\n')
        original = codebase.safe_read
        def grow_then_read(root, relative, max_bytes):
            source.write_text('#' * 20)
            return original(root, relative, max_bytes)
        with patch.object(codebase, 'safe_read', side_effect=grow_then_read):
            result = codebase.scan(self.root, self.state, max_file_bytes=100, max_total_bytes=10)
        self.assertLessEqual(result['stats']['bytes_read'], 10)
        self.assertEqual(result['files'], {})


if __name__ == '__main__':
    unittest.main()
