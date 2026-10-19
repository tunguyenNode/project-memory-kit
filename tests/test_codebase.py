import json
import os
from pathlib import Path
import tempfile
import unittest
from project_memory.codebase import scan,query,task_plan,safe_read
from project_memory import MemoryStore


class CodebaseTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.base=Path(self.temp.name);self.root=self.base/'repo';self.root.mkdir();self.state=self.base/'state'

    def tearDown(self):self.temp.cleanup()

    def write(self,path,text):
        target=self.root/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(text);return target

    def test_ast_structure_no_execution_and_incremental_update(self):
        marker=self.base/'executed'
        self.write('app.py',f"import os\nopen({str(marker)!r}, 'w').write('BAD')\nclass Service:\n    def run(self):\n        return 1\n")
        first=scan(self.root,self.state)
        self.assertFalse(marker.exists())
        self.assertEqual(first['stats']['parsed_files'],1)
        self.assertEqual(first['files']['app.py']['symbols'][0]['name'],'Service')
        self.assertTrue((self.state/'STRUCTURE.md').exists())
        second=scan(self.root,self.state)
        self.assertEqual(second['stats']['reused_files'],1)
        self.assertEqual(second['stats']['bytes_read'],0)
        self.write('app.py','def replacement():\n    return 2\n')
        self.write('new.ts','export function hello() {}\n')
        third=scan(self.root,self.state)
        self.assertEqual(third['changes']['changed'],['app.py'])
        self.assertEqual(third['changes']['added'],['new.ts'])
        self.assertEqual(third['files']['new.ts']['language'],'file_map_only')
        (self.root/'app.py').unlink()
        fourth=scan(self.root,self.state)
        self.assertEqual(fourth['changes']['removed'],['app.py'])

    def test_secrets_binary_symlink_hardlink_and_exclusions(self):
        self.write('.env','SECRET=synthetic')
        self.write('config.py','password=synthetic-not-real')
        self.write('node_modules/dep.py','def ignored(): pass')
        self.write('.git/config.txt','ignored')
        self.write('image.py','\x00binary')
        self.write('safe.py','def safe(): pass\n')
        outside=self.base/'outside.py';outside.write_text('def outside(): pass\n')
        (self.root/'linked.py').symlink_to(outside)
        (self.root/'linked_dir').symlink_to(self.base,target_is_directory=True)
        os.link(outside,self.root/'hardlink.py')
        result=scan(self.root,self.state)
        self.assertEqual(set(result['files']),{'safe.py'})
        output=(self.state/'manifest.json').read_text()+(self.state/'STRUCTURE.md').read_text()
        self.assertNotIn('synthetic-not-real',output)
        self.assertNotIn('def outside',output)
        with self.assertRaises((OSError,ValueError)):safe_read(self.root,'linked.py',1000)
        with self.assertRaises(ValueError):safe_read(self.root,'../outside.py',1000)

    def test_freshness_and_bounded_source_provenance(self):
        self.write('app.py','def calculate_total(items):\n    return sum(items)\n')
        scan(self.root,self.state)
        packed=query(self.root,self.state,'calculate_total',max_chars=2000)
        self.assertLessEqual(len(packed),2000)
        item=json.loads(packed)['matches'][0]
        self.assertEqual(item['path'],'app.py');self.assertEqual(item['start_line'],1)
        self.assertEqual(len(item['sha256']),64)
        self.write('app.py','def calculate_total(items):\n    return 0\n')
        stale=json.loads(query(self.root,self.state,'calculate_total',max_chars=2000))
        self.assertEqual(stale['matches'],[]);self.assertEqual(len(stale['warnings']),1)
        with self.assertRaises(ValueError):query(self.root,self.state,'app',max_chars=20)

    def test_partial_scan_cannot_report_deletion(self):
        for i in range(5):self.write(f'm{i}.py',f'def f{i}(): pass\n')
        scan(self.root,self.state)
        result=scan(self.root,self.state,max_files=1)
        self.assertFalse(result['complete']);self.assertEqual(result['changes']['removed'],[])
        self.assertEqual(len(result['changes']['not_indexed_or_unverified']),4)

    def test_parse_failure_drops_old_symbols(self):
        self.write('app.py','def old(): pass\n');scan(self.root,self.state)
        self.write('app.py','def invalid(:\n')
        updated=scan(self.root,self.state)
        self.assertEqual(updated['files']['app.py']['symbols'],[])
        self.assertTrue(updated['files']['app.py']['unknowns'])
        self.assertEqual(json.loads(query(self.root,self.state,'old'))['matches'],[])

    def test_size_and_state_location_guards(self):
        self.write('large.py','#' * 1000)
        result=scan(self.root,self.state,max_file_bytes=100)
        self.assertEqual(result['files'],{})
        with self.assertRaises(ValueError):scan(self.root,self.root/'state')
        with self.assertRaises(ValueError):scan(self.root,self.state,max_files=0)

    def test_empty_source_and_credential_filename(self):
        self.write('empty.py','')
        token='sk-'+'a'*24
        self.write(token+'.py','def harmless(): pass\n')
        result=scan(self.root,self.state)
        self.assertNotIn(token,json.dumps(result))
        item=json.loads(query(self.root,self.state,'empty.py'))['matches'][0]
        self.assertTrue(item['empty_source'])
        self.assertIsNone(item['start_line']);self.assertIsNone(item['end_line'])

    def test_large_synthetic_corpus_incremental(self):
        for i in range(600):self.write(f'package/module_{i}.py',f'def function_{i}():\n    return {i}\n')
        result=scan(self.root,self.state,max_files=1000)
        self.assertEqual(len(result['files']),600)
        updated=scan(self.root,self.state,max_files=1000)
        self.assertEqual(updated['stats']['parsed_files'],0)
        self.assertEqual(updated['stats']['bytes_read'],0)
        self.assertEqual(updated['stats']['reused_files'],600)

    def test_task_plan_criteria_decisions_and_no_execution(self):
        self.write('app.py','def calculate_total(items):\n    return sum(items)\n')
        self.write('tests/test_app.py','def test_total():\n    assert True\n')
        scan(self.root,self.state)
        db=self.base/'memory.db'
        with MemoryStore(db) as memory:
            memory.create_project('demo')
            memory.add('demo','decision','currency','Use decimal values','synthetic:design')
        packed=task_plan(self.root,self.state,'Add discount handling','calculate_total',criteria=['Existing totals remain unchanged without discount'],memory_db=db,project='demo',max_chars=12000)
        self.assertLessEqual(len(packed),12000)
        result=json.loads(packed)
        self.assertEqual(result['candidate_files'],['app.py'])
        self.assertEqual(result['existing_decisions'][0]['content'],'Use decimal values')
        self.assertFalse(result['needs_acceptance_criteria'])
        self.assertTrue(result['test_file_candidates']['matches'])
        self.assertIn('No code was changed or executed',result['trust'])


if __name__=='__main__':unittest.main()
