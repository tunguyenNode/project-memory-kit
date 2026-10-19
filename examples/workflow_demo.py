"""Synthetic dry run: deliberately stops because no project tests were run."""
import json
from pathlib import Path
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from project_memory.workflow import Workflow


def main():
    with tempfile.TemporaryDirectory(prefix='synthetic-workflow-') as temp:
        workflow=Workflow.create(Path(temp)/'flow.json',['Add a synthetic option'],['Default behavior remains unchanged'],['synthetic:brief'])
        plan_hash=workflow.data['plan_hash']
        workflow.submit();workflow.approve(plan_hash,'synthetic-owner');workflow.plan(plan_hash)
        for node in workflow.data['dag']:
            record={'worker_id':node['id'],'outputs':{name:'Synthetic placeholder report; no implementation was performed' for name in node['outputs']},'evidence_ids':['synthetic:placeholder']}
            if node['role']=='tester':record.update(test_outcome='not_run',test_logs='No project test command was executed in this dry run.')
            workflow.record_result(plan_hash,record)
        blocked=False
        try:workflow.review(plan_hash,workflow.results_hash(),'synthetic-reviewer','approve','Attempt to demonstrate the test-evidence gate')
        except ValueError:blocked=True
        assert blocked and workflow.data['state']=='awaiting_review'
        print(json.dumps({'mode':'synthetic_dry_run','state':workflow.data['state'],'requirement_version':1,
                          'approval_bound_to_plan_hash':True,'dag_workers_planned':len(workflow.data['dag']),
                          'workers_executed':0,'project_tests_executed':0,'reported_test_outcome':'not_run',
                          'acceptance_blocked':blocked,'reason':'No passing-test evidence; placeholders are unverified caller data.'},indent=2))

if __name__=='__main__':main()
