import unittest
from project_memory import MemoryStore
from project_memory.optional_index import OptionalHybridIndex


class OptionalIndexTests(unittest.TestCase):
    def setUp(self):
        self.store=MemoryStore(':memory:')
        self.store.create_project('alpha')
        self.store.create_project('beta')
        self.index=OptionalHybridIndex(self.store)
        if not self.index.available:
            self.skipTest('Built-in FTS5 unavailable')

    def tearDown(self):
        self.store.close()

    def add(self, content, project='alpha', **kw):
        return self.store.add(project,'fact','storage',content,'synthetic:test',**kw)

    def test_fast_path_and_zero_hit_fallback(self):
        entry=self.add('Use SQLite')
        exact=self.index.search('alpha','SQLite')
        self.assertFalse(exact.used_fallback)
        fallback=self.index.search('alpha','SQL')
        self.assertTrue(fallback.used_fallback)
        self.assertEqual([r['id'] for r in fallback.entries],[entry])

    def test_project_and_revision_filters(self):
        old=self.add('obsolete')
        new=self.add('current',supersedes=old,reason='Updated')
        self.add('foreignmarker',project='beta')
        self.assertEqual(self.index.search('alpha','obsolete').entries,[])
        self.assertEqual(self.index.search('alpha','foreignmarker').entries,[])
        self.assertEqual([r['id'] for r in self.index.search('alpha','current').entries],[new])

    def test_partial_hit_limit_is_explicit(self):
        exact=self.add('Use SQL')
        substring=self.add('Use SQLite')
        result=self.index.search('alpha','SQL')
        self.assertEqual([r['id'] for r in result.entries],[exact])
        self.assertNotEqual(result.entries,self.store.search('alpha','SQL'))
        self.assertIn('substring-only',result.recall_warning)

    def test_reopening_does_not_duplicate_index(self):
        entry=self.add('SQLite')
        reopened=OptionalHybridIndex(self.store)
        self.assertEqual([r['id'] for r in reopened.search('alpha','SQLite').entries],[entry])

    def test_blank_query_and_unavailable_index_fall_back(self):
        self.add('SQLite')
        self.assertTrue(self.index.search('alpha','').used_fallback)
        self.index.available=False
        self.assertTrue(self.index.search('alpha','SQLite').used_fallback)

    def test_fts_operators_remain_literal(self):
        self.add('SQLite')
        self.assertEqual(self.index.search('alpha','SQLite OR foreignmarker').entries,[])

    def test_token_normalization_false_positives_are_filtered(self):
        self.add('foo bar cafe')
        for query in ('foo-bar', 'foo_bar', 'café'):
            result=self.index.search('alpha',query)
            self.assertTrue(result.used_fallback)
            self.assertEqual(result.entries,self.store.search('alpha',query))

    def test_existing_records_are_indexed_on_first_open(self):
        with MemoryStore(':memory:') as old_store:
            old_store.create_project('demo')
            entry=old_store.add('demo','fact','storage','SQLite','synthetic:test')
            index=OptionalHybridIndex(old_store)
            self.assertEqual([r['id'] for r in index.search('demo','SQLite').entries],[entry])

    def test_transaction_rollback_preserves_index(self):
        before=self.index.search('alpha','rollbackword').entries
        try:
            with self.store.db:
                self.store.db.execute("INSERT INTO entries(project,kind,topic,content,source,author,observed_at,created_at) VALUES('alpha','fact','storage','rollbackword','synthetic:test','test','2026-10-19T00:00:00+00:00','2026-10-19T00:00:00+00:00')")
                raise RuntimeError('Synthetic rollback')
        except RuntimeError:
            pass
        self.assertEqual(self.index.search('alpha','rollbackword').entries,before)
