"""Run only the local harness against a pinned Click checkout; never import Click."""
import argparse, collections, hashlib, json, pathlib, shutil, subprocess, sys, time
p=argparse.ArgumentParser();p.add_argument('--kit',type=pathlib.Path,required=True);p.add_argument('--repo',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args()
kit=a.kit.resolve();repo=a.repo.resolve();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
pin='2247b35ea1c47c727d7a06e51fa280e12a863ff6'
def git(*args):return subprocess.check_output(['git','-C',str(repo),*args],text=True).strip()
assert git('rev-parse','HEAD')==pin
assert not git('status','--porcelain')
measurements={}
def cli(label,*args):
    command=[sys.executable,'-m','project_memory.codebase',*map(str,args)]
    t=time.perf_counter();r=subprocess.run(command,cwd=kit,capture_output=True,text=True);elapsed=(time.perf_counter()-t)*1000
    (out/(label+'.stdout')).write_text(r.stdout);(out/(label+'.stderr')).write_text(r.stderr)
    measurements[label]={'command':command,'exit_code':r.returncode,'wall_ms':round(elapsed,3),'stdout_chars':len(r.stdout),'stdout_utf8_bytes':len(r.stdout.encode()),'serialized_chars_excluding_cli_newline':len(r.stdout.rstrip('\n'))}
    assert r.returncode==0,(label,r.stderr)
    try:return json.loads(r.stdout)
    except json.JSONDecodeError:return r.stdout
state=out/'state'
scan=cli('scan','scan',repo,'--state',state)
manifest=json.loads((state/'manifest.json').read_text());shutil.copy2(state/'manifest.json',out/'initial-manifest.json')
exact=cli('query-exact','query',repo,'--state',state,'src/click/utils.py format_filename','--max-chars',8000)
natural=cli('query-natural','query',repo,'--state',state,'How does Click show only the basename of a filename?','--max-chars',8000)
test=cli('query-test','query',repo,'--state',state,'test_format_filename.py','--max-chars',8000)
plan=cli('task-plan','task-plan',repo,'--state',state,'--description','Explain and preserve format_filename shortening behavior','--query','src/click/utils.py format_filename','--criterion','shorten=True returns basename for /x/foo.txt','--criterion','shorten=False preserves /x/foo.txt','--max-chars',16000)
cli('handoff','handoff',repo,'--state',state)
unchanged=cli('update-unchanged','update',repo,'--state',state)
copy=out/'disposable-click';shutil.copytree(repo,copy,ignore=shutil.ignore_patterns('.git'))
copy_state=out/'copy-state';cli('copy-scan','scan',copy,'--state',copy_state)
source=copy/'src/click/utils.py';old_hash=hashlib.sha256(source.read_bytes()).hexdigest();source.write_bytes(source.read_bytes()+b'\n# Local disposable harness freshness probe.\n')
stale=cli('query-stale','query',copy,'--state',copy_state,'src/click/utils.py format_filename','--max-chars',8000)
changed=cli('update-changed','update',copy,'--state',copy_state)
fresh=cli('query-refreshed','query',copy,'--state',copy_state,'src/click/utils.py format_filename','--max-chars',8000)
assert len(exact['matches'])==1 and not exact['warnings']
assert not natural['matches']
assert any(m['path']=='tests/test_utils/test_format_filename.py' for m in plan['test_file_candidates']['matches'])
assert plan['needs_review'] is True and plan['test_relevance_unverified'] is True
assert unchanged['stats']['parsed_files']==0 and unchanged['stats']['reused_files']==scan['stats']['indexed_files']
assert not stale['matches'] and stale['warnings']
assert changed['changes']['changed']==['src/click/utils.py'] and changed['stats']['parsed_files']==1
assert fresh['matches'][0]['sha256']!=old_hash
assert not git('status','--porcelain')
tracked=git('ls-files').splitlines();python_files={x for x in tracked if x.endswith('.py')}
summary={'repository':'https://github.com/pallets/click','commit':pin,'license':'BSD-3-Clause','python':sys.version,'tracked_files':len(tracked),'tracked_python_files':len(python_files),'indexed_python_files':sum(v['language']=='python' for v in manifest['files'].values()),'indexed_symbols':sum(len(v['symbols']) for v in manifest['files'].values()),'declared_imports':sum(len(v['imports']) for v in manifest['files'].values()),'python_parse_failures':[k for k,v in manifest['files'].items() if any('parsing failed' in x for x in v['unknowns'])],'skipped_by_reason':dict(collections.Counter(x['reason'] for x in manifest['skipped'])),'scan_stats':scan['stats'],'complete_within_filters':scan['complete'],'exact_matches':len(exact['matches']),'natural_matches':len(natural['matches']),'test_matches':len(test['matches']),'task_plan_test_candidates':[m['path'] for m in plan['test_file_candidates']['matches']],'task_plan_needs_review':plan['needs_review'],'task_plan_test_relevance_unverified':plan['test_relevance_unverified'],'original_source_sha256':old_hash,'modified_source_sha256':fresh['matches'][0]['sha256'],'original_tree_clean_after':not git('status','--porcelain'),'click_code_executed':False,'click_tests_run':False,'tokens_measured':False,'measurements':measurements,'harness_source_sha256':{str(x.relative_to(kit)):hashlib.sha256(x.read_bytes()).hexdigest() for x in sorted((kit/'project_memory').glob('*.py'))}}
(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
