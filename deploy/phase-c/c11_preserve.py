"""C11 scoped preservation of old rows, versions, credentials and sandbox."""
import hashlib
import json
from pathlib import Path
from c11 import d,ROOT,HERE,WORK,OUT,SITE,WORKER,inspect,save


def run():
    sid=json.loads((OUT/'live.json').read_text())['submission_id']
    raw=d.shell('restore-only-expired-native-browser-pointer',"SID="+str(sid)+"\n"+"""import json
from pathlib import Path
from django.db import transaction
from judge.models import Profile,ContestParticipation,Submission
before=json.loads(Path('/tmp/c11-before.json').read_text());sub=Submission.objects.get(pk=SID)
old=next(p for p in before['judge.profile'] if p['id']==sub.user_id)
with transaction.atomic():
 p=Profile.objects.select_for_update().get(pk=sub.user_id)
 if p.current_contest_id!=old['current_contest_id']:
  previous=ContestParticipation.objects.get(pk=old['current_contest_id'])
  assert previous.user_id==p.pk and previous.ended
  if p.current_contest_id:
   current=ContestParticipation.objects.get(pk=p.current_contest_id)
   assert current.user_id==p.pk and current.contest_id==previous.contest_id and current.virtual!=0
  Profile.objects.filter(pk=p.pk).update(current_contest_id=previous.pk)
print('Original native pointer restored; new spectator attempt/history retained; no other profile field reset.')
""")
    code="SID="+str(sid)+"\n"+"""import json
from pathlib import Path
from django.apps import apps
from judge.models import Submission,Judge,ContestParticipation,ContestSubmission
from cpjudge.publication import verify_native
from cpjudge.models import ProblemVersion
before=json.loads(Path('/tmp/c11-before.json').read_text())
models={m._meta.label_lower:m for m in apps.get_models() if not m._meta.proxy}
after={name:list(model.objects.all().values()) for name,model in models.items()}
after=json.loads(json.dumps(after,default=str));sub=Submission.objects.get(pk=SID)
allowed={
 'auth.user':{'last_login'},
 'judge.profile':{'last_access','last_ip'},
 'cpjudge.identity':{'generation'},
 'judge.problem':{'ac_rate','user_count'},
 'judge.judge':{'online','start_time','ping','load','last_ip'},
}
changes={};failures=[];additions={};removed={}
for name,oldrows in before.items():
 pk=models[name]._meta.pk.attname
 old={r[pk]:r for r in oldrows};new={r[pk]:r for r in after[name]}
 if name=='judge.runtimeversion':
  strip=lambda rows:sorted([dict(r,**{pk:None}) for r in rows],key=lambda r:json.dumps(r,sort_keys=True))
  assert strip(oldrows)==strip(after[name]),'Native runtime inventory changed'
  continue
 for key,row in old.items():
  if key not in new:
   removed.setdefault(name,[]).append(key);continue
  diff={k for k in row if row[k]!=new[key][k]}
  if diff:
   changes.setdefault(name,[]).append({'pk':key,'fields':sorted(diff)})
   if not diff<=allowed.get(name,set()):failures.append((name,key,sorted(diff)))
   if name=='auth.user' and key!=sub.user.user_id:failures.append(('other account changed',key))
   if name=='judge.profile' and key!=sub.user_id:failures.append(('other profile changed',key))
   if name=='cpjudge.identity' and row['user_id']!=sub.user.user_id:failures.append(('other identity changed',key))
   if name=='judge.problem' and key!=sub.problem_id:failures.append(('other problem changed',key))
 added=[r for key,r in new.items() if key not in old]
 if added:additions[name]=len(added)
 if name=='judge.submission':assert [r['id'] for r in added]==[SID]
 elif name=='judge.submissionsource':assert len(added)==1 and added[0]['submission_id']==SID
 elif name=='judge.submissiontestcase':assert len(added)==103 and all(r['submission_id']==SID for r in added)
 elif name=='judge.contestparticipation':
  assert len(added)==1 and added[0]['user_id']==sub.user_id and added[0]['contest_id']==sub.contest_object_id and added[0]['virtual']!=0
 elif name=='judge.contestsubmission':
  assert len(added)==1 and added[0]['submission_id']==SID
 elif added:failures.append(('unexpected additions',name,len(added)))
assert not removed,removed
assert not failures,failures
assert not Submission.objects.filter(status__in=Submission.IN_PROGRESS_GRADING_STATUS).exists()
for version in ProblemVersion.objects.filter(state='published').select_related('problem'):assert verify_native(version)
j=Judge.objects.get(name='cpjudge-local-worker');assert j.online and not j.is_blocked
assert list(j.problems.values_list('code',flat=True))==['pv000000000000000001']
assert list(j.runtimes.order_by('key').values_list('key',flat=True))==['CPP11','CPP14','CPP17','CPP20','CPP23']
print('C11_PRESERVED='+json.dumps({'status':'PASS','model_sets':len(before),'prior_rows':sum(map(len,before.values())),
 'existing_rows_preserved_except_expected_native_activity':changes,'added_rows':additions,
 'passwords_ids_emails_audits_versions_prior_source_results_contests_unchanged':True,
 'published_versions_verified':ProblemVersion.objects.filter(state='published').count(),
 'worker_online_original_problem_and_runtime_memberships':True,'no_pending_jobs':True,
 'browser_created_one_native_unranked_spectator_context':True,'original_profile_contest_pointer_restored':True}))
"""
    raw=d.shell('preserve-all-original-models',code)
    result=json.loads(raw.decode().split('C11_PRESERVED=',1)[1].splitlines()[0])
    from tools.site_problem import file_manifest
    before=json.loads((WORK/'files-before.json').read_text())
    assert file_manifest(ROOT/'build/b03-worker-1/problems')==before.pop('worker_files')
    for path,digest in before.items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest,path
    containers=json.loads((WORK/'containers-before.json').read_text())
    for name,old in containers.items():
        current=inspect(name)
        for key in ('Id','Image','Config','HostConfig','Mounts'):
            assert current[key]==old[key],(name,key)
        if name!=WORKER:assert current['State']['StartedAt']==old['State']['StartedAt']
    result.update({'worker_files_registry_credentials_unchanged':True,'container_ids_images_config_mounts_sandbox_unchanged':True,
                   'only_worker_container_restarted_for_C11':True,'schema_changed':False})
    save('preservation.json',result)
    d.docker('migration-consistency','exec',SITE,'python','manage.py','makemigrations','--check','--dry-run')
    d.run('readiness-lifecycle-idempotent',['python3','-B',str(ROOT/'deploy/site-local/worker_readiness.py'),'start'])
    print('PASS: all prior data, credentials, immutable versions, containers and sandbox preserved.')
