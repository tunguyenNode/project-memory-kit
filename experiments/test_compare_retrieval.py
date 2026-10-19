"""Isolated experiment checks; synthetic fixtures, no external services."""
import json
import unittest
from experiments.compare_retrieval import Indexes, pack, seed
from project_memory import MemoryStore


class ExperimentChecks(unittest.TestCase):
    def setUp(self):
        self.store = MemoryStore(':memory:')
        self.fixtures = seed(self.store, 20)
        self.indexes = Indexes(self.store)

    def tearDown(self):
        self.store.close()

    def test_expected_indexed_fixture_semantics(self):
        for fixture in self.fixtures:
            expected = [] if fixture['name'] in ('paraphrase_gap', 'substring_gap') else fixture['ids']
            for materialized in (False, True):
                rows = self.indexes.search('alpha', fixture['query'], materialized)
                self.assertEqual(sorted(row['id'] for row in rows), sorted(expected))
                self.assertTrue(all(row['project'] == 'alpha' for row in rows))

    def test_trigger_mutation_rolls_back_atomically(self):
        first = self.store.add('alpha', 'decision', 'rollback', 'First', 'synthetic:test')
        try:
            with self.store.db:
                self.store.db.execute('''INSERT INTO entries
                    (project,kind,topic,content,source,author,observed_at,created_at,supersedes)
                    SELECT project,kind,topic,?,source,author,observed_at,created_at,id
                    FROM entries WHERE id=?''', ('Second', first))
                self.assertEqual(self.indexes.search('alpha', 'rollback', True)[0]['content'], 'Second')
                raise RuntimeError('Synthetic forced rollback')
        except RuntimeError:
            pass
        for materialized in (False, True):
            self.assertEqual([row['id'] for row in self.indexes.search('alpha', 'rollback', materialized)], [first])

    def test_query_operators_are_literal(self):
        for query in ('" OR *', "'); DROP TABLE entries; --", 'storage OR foreignmarker'):
            self.assertEqual(self.indexes.search('alpha', query), [])
        self.assertEqual(len(self.indexes.search('alpha', 'storage')), 1)

    def test_default_pack_bound_and_accounting(self):
        rows = self.store.search('alpha', include_history=True)
        output = pack(rows)
        self.assertLessEqual(len(output.encode('utf-8')), 8000)
        decoded = json.loads(output)
        self.assertEqual(len(decoded['entries']) + decoded['omitted'], len(rows))


if __name__ == '__main__':
    unittest.main()
