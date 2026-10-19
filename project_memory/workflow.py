"""Local dry-run checkpoints. Never starts agents, shells, models or tests."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from datetime import datetime, timezone
from .codebase import atomic_write
from .store import check_text

MAX_RECORD_BYTES=65536
ROLES={'architect','implementer','tester','reviewer'}


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()).hexdigest()


def timestamp():return datetime.now(timezone.utc).isoformat()


def text(value,label):
    if not isinstance(value,str) or not value.strip():raise ValueError(label+' must be nonempty text')
    check_text(value)
    return value


def strings(values,label,allow_empty=False):
    if not isinstance(values,list) or (not values and not allow_empty):raise ValueError(label+' must be a list')
    for value in values:text(value,label)
    if len(values)!=len(set(values)):raise ValueError(label+' must not contain duplicates')
    return values


def requirements(version,scope,criteria,evidence):
    return {'version':version,'scope':strings(scope,'scope'),'acceptance_criteria':strings(criteria,'acceptance criteria'),
            'evidence_ids':strings(evidence,'evidence IDs',allow_empty=True)}


def default_dag():
    return [
        {'id':'architect','role':'architect','depends_on':[],'outputs':['design_notes']},
        {'id':'implementer','role':'implementer','depends_on':['architect'],'outputs':['change_summary']},
        {'id':'tester','role':'tester','depends_on':['implementer'],'outputs':['test_report']},
        {'id':'reviewer','role':'reviewer','depends_on':['tester'],'outputs':['review_report']},
    ]


def validate_dag(nodes):
    if not isinstance(nodes,list) or not 1<=len(nodes)<=100:raise ValueError('DAG must contain 1–100 worker specifications')
    by_id={}
    for node in nodes:
        if not isinstance(node,dict) or set(node)!={'id','role','depends_on','outputs'}:raise ValueError('Invalid worker specification')
        identifier=text(node['id'],'worker ID')
        if identifier in by_id:raise ValueError('Duplicate worker ID')
        if node['role'] not in ROLES:raise ValueError('Unsupported worker role')
        strings(node['depends_on'],'dependencies',allow_empty=True);strings(node['outputs'],'declared outputs')
        by_id[identifier]=node
    if {n['role'] for n in nodes}!=ROLES:raise ValueError('DAG must include architect, implementer, tester and reviewer roles')
    for node in nodes:
        if any(dep not in by_id for dep in node['depends_on']):raise ValueError('Unknown dependency')
    visiting=set();visited=set()
    def visit(identifier):
        if identifier in visiting:raise ValueError('Dependency cycle')
        if identifier in visited:return
        visiting.add(identifier)
        for dep in by_id[identifier]['depends_on']:visit(dep)
        visiting.remove(identifier);visited.add(identifier)
    for identifier in by_id:visit(identifier)
    return nodes


class Workflow:
    """Single-writer JSON state. Labels are claims, not authenticated identities.

    The owner can edit the file; this is not a tamper-proof permission boundary.
    """
    def __init__(self,path):
        self.path=Path(path)
        if self.path.stat().st_size>4194304:raise ValueError('Workflow file exceeds local size limit')
        raw=self.path.read_bytes()
        self._disk_hash=hashlib.sha256(raw).hexdigest()
        self._persisted_raw=raw
        self.data=json.loads(raw)
        if not isinstance(self.data,dict):raise ValueError('Workflow must be a JSON object')
        if self.data.get('schema')!=1:raise ValueError('Unsupported workflow schema')
        for field,kind in {'requirements':dict,'plan_hash':str,'events':list,'history':list,'dag':list,'results':dict,'state':str}.items():
            if not isinstance(self.data.get(field),kind):raise ValueError('Invalid workflow schema')
        if digest(self.data['requirements'])!=self.data['plan_hash']:raise ValueError('Requirement hash mismatch')

    @classmethod
    def create(cls,path,scope,criteria,evidence_ids=None):
        path=Path(path)
        if path.exists():raise ValueError('Workflow already exists')
        plan=requirements(1,scope,criteria,evidence_ids or [])
        data={'schema':1,'mode':'dry_run','state':'draft','requirements':plan,'plan_hash':digest(plan),
              'approval':None,'dag':[],'results':{},'review':None,'acceptance':None,'history':[],
              'events':[{'type':'created','at':timestamp()}],
              'trust':'Caller-provided planning/result data. No agents, code or tests execute. Actor labels and evidence references are not authenticated or verified.'}
        encoded=json.dumps(data,ensure_ascii=True,indent=2)
        if len(encoded.encode())>4194304:raise ValueError('Workflow state exceeds local size limit')
        path.parent.mkdir(parents=True,exist_ok=True)
        # Exclusive create avoids silently replacing an existing checkpoint.
        with path.open('x') as handle:handle.write(encoded)
        return cls(path)

    def _save(self,event):
        try:
            if hashlib.sha256(self.path.read_bytes()).hexdigest()!=self._disk_hash:
                raise ValueError('Workflow changed on disk; reload before applying a checkpoint')
            self.data['events'].append({'type':event,'at':timestamp()})
            encoded=json.dumps(self.data,ensure_ascii=True,indent=2)
            if len(encoded.encode())>4194304:raise ValueError('Workflow state exceeds local size limit')
            atomic_write(self.path,encoded)
            self._persisted_raw=encoded.encode()
            self._disk_hash=hashlib.sha256(self._persisted_raw).hexdigest()
        except (OSError,ValueError,TypeError):
            self.data=json.loads(self._persisted_raw)
            raise
        return self.data

    def _hash(self,plan_hash):
        if plan_hash!=self.data['plan_hash'] or digest(self.data['requirements'])!=plan_hash:
            raise ValueError('Exact current requirement-plan hash is required')

    def _approved(self,plan_hash):
        self._hash(plan_hash)
        if not self.data['approval'] or self.data['approval']['plan_hash']!=plan_hash:
            raise ValueError('Current requirements must be explicitly approved first')

    def results_hash(self):
        return digest({'plan_hash':self.data['plan_hash'],'dag':self.data['dag'],'results':self.data['results']})

    def edit(self,scope,criteria,evidence_ids=None):
        plan=requirements(self.data['requirements']['version']+1,scope,criteria,evidence_ids or [])
        self.data['history'].append({k:self.data[k] for k in ('requirements','plan_hash','approval','dag','results','review','acceptance')})
        self.data.update(requirements=plan,plan_hash=digest(plan),state='draft',approval=None,dag=[],results={},review=None,acceptance=None)
        return self._save('requirements_edited_all_approvals_invalidated')

    def submit(self):
        if self.data['state']!='draft':raise ValueError('Only a draft can be submitted for requirements approval')
        self.data['state']='awaiting_requirements'
        return self._save('requirements_submitted')

    def approve(self,plan_hash,actor):
        self._hash(plan_hash);text(actor,'approving actor label')
        if self.data['state']!='awaiting_requirements':raise ValueError('Requirements are not awaiting approval')
        self.data['approval']={'plan_hash':plan_hash,'actor_label':actor,'at':timestamp(),'identity_verified':False}
        self.data['state']='approved'
        return self._save('requirements_approved_by_caller')

    def plan(self,plan_hash,nodes=None):
        self._approved(plan_hash)
        if self.data['state']!='approved':raise ValueError('Worker DAG can be set only after requirements approval')
        self.data['dag']=validate_dag(nodes if nodes is not None else default_dag())
        self.data['state']='planned'
        return self._save('worker_dag_recorded_no_workers_started')

    def record_result(self,plan_hash,record):
        self._approved(plan_hash)
        if self.data['state'] not in {'planned','awaiting_review','awaiting_acceptance'}:raise ValueError('Workflow is not accepting results')
        if not isinstance(record,dict) or set(record)-{'worker_id','outputs','evidence_ids','test_outcome','test_logs','candidate_issues'}:
            raise ValueError('Invalid result schema')
        if len(json.dumps(record).encode())>MAX_RECORD_BYTES:raise ValueError('Result exceeds record-size limit')
        check_text(json.dumps(record))
        worker_id=text(record.get('worker_id'),'worker ID')
        node=next((n for n in self.data['dag'] if n['id']==worker_id),None)
        if not node:raise ValueError('Unknown worker')
        if any(dep not in self.data['results'] for dep in node['depends_on']):raise ValueError('Dependency results are missing')
        outputs=record.get('outputs')
        if not isinstance(outputs,dict) or set(outputs)!=set(node['outputs']):raise ValueError('Result must supply exactly the declared outputs')
        for value in outputs.values():text(value,'output reference or summary')
        strings(record.get('evidence_ids',[]),'result evidence IDs',allow_empty=True)
        if node['role']=='tester':
            if record.get('test_outcome') not in {'pass','fail','not_run','unknown'}:raise ValueError('Tester must explicitly report pass, fail, not_run or unknown')
            text(record.get('test_logs'),'caller-provided test log or not-run explanation')
        elif 'test_outcome' in record or 'test_logs' in record:raise ValueError('Only tester records may report tests')
        issues=record.get('candidate_issues',[])
        if not isinstance(issues,list):raise ValueError('Candidate issues must be a list')
        normalized=[]
        for issue in issues:
            if not isinstance(issue,dict) or set(issue)!={'description','evidence_ids','confidence'}:raise ValueError('Invalid candidate issue schema')
            text(issue['description'],'candidate issue description');strings(issue['evidence_ids'],'candidate evidence IDs')
            if issue['confidence'] not in {'low','medium','high'}:raise ValueError('Confidence must be low, medium or high')
            normalized.append({**issue,'status':'unverified_candidate','confidence_source':'caller_claim'})
        # Replacing upstream evidence invalidates dependent results and any review/acceptance.
        affected={worker_id}
        while True:
            more={n['id'] for n in self.data['dag'] if any(d in affected for d in n['depends_on'])}
            if more<=affected:break
            affected|=more
        for identifier in affected:self.data['results'].pop(identifier,None)
        stored={**record,'candidate_issues':normalized,'plan_hash':plan_hash,'status':'caller_supplied_unverified','recorded_at':timestamp()}
        self.data['results'][worker_id]=stored
        self.data['review']=None;self.data['acceptance']=None
        self.data['state']='awaiting_review' if len(self.data['results'])==len(self.data['dag']) else 'planned'
        return self._save('caller_result_recorded_review_invalidated')

    def review(self,plan_hash,results_hash,actor,decision,notes):
        self._approved(plan_hash);text(actor,'reviewer label');text(notes,'review notes')
        if self.data['state']!='awaiting_review':raise ValueError('Complete results must await review first')
        if results_hash!=self.results_hash():raise ValueError('Exact current result-set hash is required')
        if decision not in {'approve','request_changes'}:raise ValueError('Review must approve or request_changes')
        if decision=='approve':
            for node in self.data['dag']:
                item=self.data['results'].get(node['id'])
                if not item or item['plan_hash']!=plan_hash:raise ValueError('Missing or stale worker result')
                if node['role']=='tester' and (item.get('test_outcome')!='pass' or not item.get('evidence_ids')):
                    raise ValueError('Acceptance requires caller-reported passing tests with evidence references')
        self.data['review']={'plan_hash':plan_hash,'results_hash':results_hash,'actor_label':actor,'decision':decision,
                             'notes':notes,'at':timestamp(),'status':'caller_review_attestation','identity_verified':False}
        self.data['state']='awaiting_acceptance' if decision=='approve' else 'planned'
        return self._save('review_attestation_recorded')

    def accept(self,plan_hash,results_hash,actor):
        self._approved(plan_hash);text(actor,'accepting actor label')
        review=self.data['review']
        if self.data['state']!='awaiting_acceptance' or not review or review['decision']!='approve':raise ValueError('Approved review and passing-test evidence are required before acceptance')
        if results_hash!=self.results_hash() or review['results_hash']!=results_hash or review['plan_hash']!=plan_hash:
            raise ValueError('Stale result review or plan')
        self.data['acceptance']={'plan_hash':plan_hash,'results_hash':results_hash,'actor_label':actor,'at':timestamp(),'identity_verified':False}
        self.data['state']='accepted'
        return self._save('accepted_by_caller_no_execution_claim')


def read_record(path):
    path=Path(path)
    if path.stat().st_size>MAX_RECORD_BYTES:raise ValueError('Input record exceeds size limit')
    return json.loads(path.read_text())


def main(argv=None):
    p=argparse.ArgumentParser(description='Local dry-run requirement and delivery checkpoints; no worker execution')
    subs=p.add_subparsers(dest='command',required=True)
    for command in ('create','edit','show','submit','approve','plan','result','review','accept'):
        sub=subs.add_parser(command);sub.add_argument('file')
        if command in {'create','edit'}:
            sub.add_argument('--scope',action='append',required=True);sub.add_argument('--criterion',action='append',required=True);sub.add_argument('--evidence',action='append',default=[])
        if command in {'approve','plan','result','review','accept'}:sub.add_argument('--hash',required=True)
        if command in {'approve','review','accept'}:sub.add_argument('--actor',required=True)
        if command=='plan':sub.add_argument('--dag-json')
        if command=='result':sub.add_argument('--record-json',required=True)
        if command in {'review','accept'}:sub.add_argument('--results-hash',required=True)
        if command=='review':sub.add_argument('--decision',choices=['approve','request_changes'],required=True);sub.add_argument('--notes',required=True)
    args=p.parse_args(argv)
    try:
        if args.command=='create':flow=Workflow.create(args.file,args.scope,args.criterion,args.evidence)
        else:
            flow=Workflow(args.file)
            if args.command=='edit':flow.edit(args.scope,args.criterion,args.evidence)
            elif args.command=='submit':flow.submit()
            elif args.command=='approve':flow.approve(args.hash,args.actor)
            elif args.command=='plan':flow.plan(args.hash,read_record(args.dag_json) if args.dag_json else None)
            elif args.command=='result':flow.record_result(args.hash,read_record(args.record_json))
            elif args.command=='review':flow.review(args.hash,args.results_hash,args.actor,args.decision,args.notes)
            elif args.command=='accept':flow.accept(args.hash,args.results_hash,args.actor)
        result={**flow.data,'current_results_hash':flow.results_hash()}
        print(json.dumps(result,ensure_ascii=True,indent=2));return 0
    except (OSError,ValueError,KeyError,TypeError,RecursionError):
        print('Checkpoint rejected. Check state, exact hashes, prerequisites and input schema. No worker or test was executed.',file=sys.stderr);return 2


if __name__=='__main__':sys.exit(main())
