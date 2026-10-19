"""Synthetic legacy-repository onboarding demo. No scanned code is executed."""
import json
from pathlib import Path
import sys
import tempfile
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from project_memory.codebase import scan,query,task_plan


def main():
    with tempfile.TemporaryDirectory(prefix='synthetic-codebase-demo-') as temp:
        base=Path(temp);root=base/'legacy';root.mkdir();state=base/'state'
        package=root/'package';package.mkdir()
        for i in range(1000):
            (package/f'module_{i}.py').write_text(f'def calculate_{i}(value):\n    return value + {i}\n')
        tests=root/'tests';tests.mkdir();(tests/'test_total.py').write_text('def test_total():\n    assert True\n')
        (root/'.env').write_text('password=synthetic-not-real')
        start=time.perf_counter();initial=scan(root,state);first_ms=(time.perf_counter()-start)*1000
        start=time.perf_counter();unchanged=scan(root,state);update_ms=(time.perf_counter()-start)*1000
        (package/'module_42.py').write_text('def calculate_42(value):\n    return value + 100\n')
        stale=json.loads(query(root,state,'module_42.py calculate_42',max_chars=2000))
        (package/'module_99.py').unlink()
        refreshed=scan(root,state)
        pack=query(root,state,'module_42.py calculate_42',max_chars=2000)
        plan=task_plan(root,state,'Investigate an incorrect total and prepare an approved change','module_42.py calculate_42',criteria=['Describe the expected total before changing code'],max_chars=12000)
        assert stale['matches']==[] and stale['warnings']
        assert len(pack)<=2000 and len(plan)<=12000
        assert refreshed['changes']['changed']==['package/module_42.py']
        assert refreshed['changes']['removed']==['package/module_99.py']
        assert unchanged['stats']['bytes_read']==0
        print(json.dumps({'fixture':'1000 synthetic modules + one synthetic test; .env excluded',
            'initial_scan':{'stats':initial['stats'],'elapsed_ms':round(first_ms,3)},
            'unchanged_update':{'stats':unchanged['stats'],'elapsed_ms':round(update_ms,3)},
            'changed_update':{'stats':refreshed['stats'],'changes':refreshed['changes']},
            'stale_query_rejected':True,'query_pack_chars':len(pack),'task_plan_chars':len(plan),
            'tokens_measured':False,'source_code_executed':False,
            'limits':'Single local synthetic run, not a real-project speed guarantee. Unchanged update trusts metadata stamps; selected query sources are rehashed. No root cause, runtime dependency graph or test result is inferred.'},indent=2))

if __name__=='__main__':main()
