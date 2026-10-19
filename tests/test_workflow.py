import copy
from pathlib import Path
import tempfile
import unittest
from project_memory.workflow import Workflow,default_dag


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/'workflow.json'
        self.flow=Workflow.create(self.path,['Add a synthetic option'],['Default behavior stays unchanged'],['synthetic:requirement'])
        self.hash=self.flow.data['plan_hash']

    def tearDown(self):self.temp.cleanup()

    def plan(self):
        self.flow.submit();self.flow.approve(self.hash,'synthetic-owner');self.flow.plan(self.hash)

    def record(self,worker,outcome='pass'):
        node=next(n for n in self.flow.data['dag'] if n['id']==worker)
        result={'worker_id':worker,'outputs':{name:'Synthetic report only' for name in node['outputs']},'evidence_ids':['synthetic:'+worker]}
        if worker=='tester':result.update(test_outcome=outcome,test_logs='Synthetic caller-supplied test log; not executed by harness')
        return self.flow.record_result(self.hash,result)

    def complete_results(self,outcome='pass'):
        for role in ['architect','implementer','tester','reviewer']:self.record(role,outcome)

    def test_approval_cannot_be_bypassed(self):
        with self.assertRaises(ValueError):self.flow.approve(self.hash,'owner')
        with self.assertRaises(ValueError):self.flow.plan(self.hash)
        with self.assertRaises(ValueError):self.flow.accept(self.hash,self.flow.results_hash(),'owner')
        self.assertEqual(Workflow(self.path).data['state'],'draft')

    def test_wrong_hash_and_old_approval_replay(self):
        self.flow.submit()
        with self.assertRaises(ValueError):self.flow.approve('0'*64,'owner')
        self.flow.approve(self.hash,'owner')
        self.flow.edit(['Expanded synthetic scope'],['New criterion'],['synthetic:revision'])
        self.assertNotEqual(self.hash,self.flow.data['plan_hash'])
        self.assertIsNone(self.flow.data['approval'])
        self.assertEqual(self.flow.data['state'],'draft')
        with self.assertRaises(ValueError):self.flow.plan(self.hash)
        self.flow.submit()
        with self.assertRaises(ValueError):self.flow.approve(self.hash,'owner')

    def test_cycle_rejected(self):
        self.flow.submit();self.flow.approve(self.hash,'owner')
        dag=default_dag();dag[0]['depends_on']=['reviewer']
        with self.assertRaises(ValueError):self.flow.plan(self.hash,dag)
        self.assertEqual(self.flow.data['state'],'approved')

    def test_missing_dependency_result_rejected(self):
        self.plan()
        with self.assertRaises(ValueError):self.record('implementer')
        self.assertEqual(self.flow.data['results'],{})

    def test_missing_tests_and_review_block_acceptance(self):
        self.plan();self.record('architect');self.record('implementer')
        with self.assertRaises(ValueError):self.flow.review(self.hash,self.flow.results_hash(),'reviewer','approve','Checked')
        with self.assertRaises(ValueError):self.flow.accept(self.hash,self.flow.results_hash(),'owner')
        self.record('tester');self.record('reviewer')
        self.assertEqual(self.flow.data['state'],'awaiting_review')
        with self.assertRaises(ValueError):self.flow.accept(self.hash,self.flow.results_hash(),'owner')

    def test_failed_or_not_run_tests_cannot_pass_gate(self):
        self.plan();self.complete_results('not_run')
        with self.assertRaises(ValueError):self.flow.review(self.hash,self.flow.results_hash(),'reviewer','approve','Checked')
        self.assertEqual(self.flow.data['state'],'awaiting_review')
        self.flow.review(self.hash,self.flow.results_hash(),'reviewer','request_changes','Need actual test evidence')
        self.record('tester','fail');self.record('reviewer')
        with self.assertRaises(ValueError):self.flow.review(self.hash,self.flow.results_hash(),'reviewer','approve','Checked')

    def test_reviewed_acceptance_is_explicit_and_hash_bound(self):
        self.plan();self.complete_results()
        results_hash=self.flow.results_hash()
        with self.assertRaises(ValueError):self.flow.review(self.hash,'0'*64,'reviewer','approve','Checked')
        self.flow.review(self.hash,results_hash,'synthetic-reviewer','approve','Caller attests evidence was reviewed')
        self.assertEqual(self.flow.data['state'],'awaiting_acceptance')
        with self.assertRaises(ValueError):self.flow.accept(self.hash,'0'*64,'owner')
        self.flow.accept(self.hash,results_hash,'synthetic-owner')
        self.assertEqual(self.flow.data['state'],'accepted')
        self.assertFalse(self.flow.data['acceptance']['identity_verified'])

    def test_replacing_upstream_result_invalidates_review_and_descendants(self):
        self.plan();self.complete_results()
        previous=self.flow.results_hash()
        self.flow.review(self.hash,previous,'reviewer','approve','Reviewed')
        self.record('implementer')
        self.assertEqual(set(self.flow.data['results']),{'architect','implementer'})
        self.assertIsNone(self.flow.data['review']);self.assertEqual(self.flow.data['state'],'planned')
        with self.assertRaises(ValueError):self.flow.accept(self.hash,previous,'owner')

    def test_candidate_issue_is_not_verified_bug(self):
        self.plan()
        self.flow.record_result(self.hash,{'worker_id':'architect','outputs':{'design_notes':'Synthetic findings'},'evidence_ids':['synthetic:line'],
            'candidate_issues':[{'description':'Possible missing boundary check','evidence_ids':['synthetic:line'],'confidence':'high'}]})
        issue=self.flow.data['results']['architect']['candidate_issues'][0]
        self.assertEqual(issue['status'],'unverified_candidate')
        self.assertEqual(self.flow.data['results']['architect']['status'],'caller_supplied_unverified')

    def test_scope_change_clears_accepted_state(self):
        self.plan();self.complete_results();h=self.flow.results_hash()
        self.flow.review(self.hash,h,'reviewer','approve','Reviewed');self.flow.accept(self.hash,h,'owner')
        self.flow.edit(['Different scope'],['Different criterion'],[])
        self.assertEqual(self.flow.data['requirements']['version'],2)
        self.assertIsNone(self.flow.data['acceptance']);self.assertEqual(self.flow.data['results'],{})
        self.assertEqual(len(self.flow.data['history']),1)

    def test_no_fake_pass_or_output_override(self):
        self.plan();self.record('architect');self.record('implementer')
        with self.assertRaises(ValueError):self.flow.record_result(self.hash,{'worker_id':'tester','outputs':{'test_report':'No execution'},'evidence_ids':[]})
        with self.assertRaises(ValueError):self.flow.record_result(self.hash,{'worker_id':'tester','outputs':{'test_report':'No execution'},'evidence_ids':[], 'test_outcome':'pass','test_logs':''})

    def test_reported_pass_without_evidence_is_not_acceptable(self):
        self.plan();self.record('architect');self.record('implementer')
        self.flow.record_result(self.hash,{'worker_id':'tester','outputs':{'test_report':'Reported pass'},'evidence_ids':[], 'test_outcome':'pass','test_logs':'Caller claim'})
        self.record('reviewer')
        with self.assertRaises(ValueError):self.flow.review(self.hash,self.flow.results_hash(),'reviewer','approve','Checked')

    def test_old_loaded_state_cannot_overwrite_edited_plan(self):
        stale=Workflow(self.path)
        self.flow.edit(['New current scope'],['New criterion'],[])
        with self.assertRaises(ValueError):stale.submit()
        current=Workflow(self.path)
        self.assertEqual(current.data['requirements']['version'],2)
        self.assertEqual(current.data['state'],'draft')


if __name__=='__main__':unittest.main()
