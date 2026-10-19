"""Synthetic Click-shaped layout; no third-party repository is vendored."""
import json
from pathlib import Path
import tempfile
import unittest
from project_memory.codebase import scan,task_plan,test_candidates as select_test_candidates


class TaskTestSelectionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.base=Path(self.temp.name)
        self.root=self.base/'repo';self.root.mkdir();self.state=self.base/'state'
        self.write('src/click/utils.py','def format_filename(value):\n    return str(value)\n')
        for name in ('a-tests.yml','b-tests.yml','c-tests.yml','d-tests.yml'):
            self.write('.github/workflows/'+name,'name: tests\n')
        self.write('conftest.py','def pytest_configure():\n    pass\n')
        self.write('tests/conftest.py','def pytest_configure():\n    pass\n')
        self.write('tests/test_other.py','def test_other():\n    assert True\n')
        self.write('tests/test_utils/test_format_filename.py','def test_format_filename():\n    assert True\n')
        scan(self.root,self.state)

    def tearDown(self):self.temp.cleanup()

    def write(self,name,content):
        p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(content)

    def test_symbol_test_prioritized_over_ci_and_conftest(self):
        raw=task_plan(self.root,self.state,'Investigate filename formatting','src/click/utils.py format_filename',criteria=['Confirm expected filename output'],max_chars=12000)
        plan=json.loads(raw);tests=plan['test_file_candidates']
        self.assertLessEqual(len(raw),12000)
        self.assertEqual(tests['matches'][0]['path'],'tests/test_utils/test_format_filename.py')
        self.assertEqual(len(tests['matches'][0]['sha256']),64)
        self.assertTrue(tests['matches'][0]['verified_at'])
        self.assertTrue(plan['needs_review']);self.assertTrue(plan['human_review_required'])
        self.assertTrue(plan['test_relevance_unverified']);self.assertTrue(tests['test_relevance_unverified'])
        self.assertEqual(tests['selection_method'],'filename_and_symbol_heuristic')

    def test_ranked_test_still_requires_fresh_hash(self):
        self.write('tests/test_utils/test_format_filename.py','def test_format_filename():\n    assert False\n')
        result=json.loads(select_test_candidates(self.root,self.state,'src/click/utils.py format_filename',['src/click/utils.py'],max_chars=3000))
        self.assertNotIn('tests/test_utils/test_format_filename.py',[m['path'] for m in result['matches']])
        self.assertIn('tests/test_utils/test_format_filename.py',[w['path'] for w in result['warnings']])

    def test_large_high_rank_excerpt_is_shortened_to_budget(self):
        source='def test_format_filename():\n'+''.join('    value = '+repr('synthetic data '*10)+'\n' for _ in range(90))
        self.write('tests/test_utils/test_format_filename.py',source);scan(self.root,self.state)
        raw=select_test_candidates(self.root,self.state,'format_filename',['src/click/utils.py'],max_chars=2000,max_results=1)
        self.assertLessEqual(len(raw),2000)
        result=json.loads(raw);self.assertEqual(len(result['matches']),1)
        self.assertFalse(result['matches'][0]['excerpt_complete_symbol'])
        self.assertLess(result['matches'][0]['end_line'],80)

    def test_declared_test_filename_is_prioritized(self):
        result=json.loads(select_test_candidates(self.root,self.state,'test_other.py',[],max_chars=3000))
        self.assertEqual(result['matches'][0]['path'],'tests/test_other.py')
        self.assertTrue(result['test_relevance_unverified'])


if __name__=='__main__':unittest.main()
