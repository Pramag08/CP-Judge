"""C12 bounded acceptance only; private raw evidence, no service reload."""
import hashlib
import json
import os
import sys
from pathlib import Path
import c05 as d

ROOT, HERE, SITE = d.ROOT, d.HERE, d.SITE
WORK = ROOT / 'build/phase-c-c12-1'
OUT = ROOT / 'reports/phase-c-c12-1'
WORK.mkdir(parents=True, exist_ok=True, mode=0o700)
OUT.mkdir(parents=True, exist_ok=True)
d.WORK, d.OUT = WORK, OUT

SNAPSHOT = '''import hashlib,json
from pathlib import Path
from django.apps import apps
from cpjudge.imports import private_root
from judge.models import Submission
assert not Submission.objects.filter(status__in=Submission.IN_PROGRESS_GRADING_STATUS).exists()
def files():
 return {str(p.relative_to(private_root())):hashlib.sha256(p.read_bytes()).hexdigest() for p in private_root().rglob('*') if p.is_file()}
def rows():
 return json.loads(json.dumps({m._meta.label_lower:list(m.objects.all().values()) for m in apps.get_models() if not m._meta.proxy},default=str))
'''

action = sys.argv[1]
if action == 'snapshot':
    d.shell('private-preservation-baseline', SNAPSHOT + '''
p=Path('/tmp/c12-before.json');assert not p.exists()
p.write_text(json.dumps({'rows':rows(),'files':files()}));p.chmod(0o600)
print('Saved private all-model and import-file baseline; no active judging.')
''')
    baseline = {}
    for name in (SITE, 'cpjudge-b03-worker', 'cpjudge-b01-db', 'cpjudge-b01-redis'):
        obj = json.loads(d.docker('snapshot-container-' + name, 'inspect', name))[0]
        baseline[name] = hashlib.sha256(json.dumps({k: obj[k] for k in ('Id', 'Image', 'Config', 'HostConfig', 'Mounts')}, sort_keys=True).encode()).hexdigest()
    (WORK / 'containers.json').write_text(json.dumps(baseline))
elif action == 'prepare-isolation-fixture':
    d.shell('prepare-only-task-fixture-import-grant', '''import io,json,uuid,zipfile
from pathlib import Path
from django.contrib.auth import get_user_model
from judge.models import Contest
from cpjudge.models import ImportJob
from cpjudge.imports import private_root
from cpjudge.policy import grant_scope
before=json.loads(Path('/tmp/c12-before.json').read_text())
old={r['id'] for r in before['rows']['cpjudge.importjob']}
jobs=list(ImportJob.objects.exclude(pk__in=old));assert len(jobs)<=1
if jobs:
 job=jobs[0];assert job.owner.username=='C1LIVEA' and job.status=='uploaded' and job.attempt==0
 source=private_root()/job.archive_key
 with zipfile.ZipFile(source) as z:assert z.namelist()==['c12-acceptance.txt']
 data=source.read_bytes()
else:
 buffer=io.BytesIO()
 with zipfile.ZipFile(buffer,'w') as z:z.writestr('c12-acceptance.txt',uuid.uuid4().hex)
 data=buffer.getvalue()
p=Path('/tmp/c12-race.zip');assert not p.exists();p.write_bytes(data);p.chmod(0o600)
U=get_user_model();actor=U.objects.filter(is_active=True,is_superuser=True).exclude(username='C1LIVEADMIN').order_by('pk').first()
grant_scope(actor,U.objects.get(username='C1LIVEB'),Contest.objects.get(key='c1liveb'),'problems.import')
print('Second task-owned author granted own-contest import; original race ZIP retained for retry.')
''')
    d.docker('retain-private-race-fixture', 'cp', SITE + ':/tmp/c12-race.zip', str(WORK / 'race.zip'))
    (WORK / 'race.zip').chmod(0o600)
elif action == 'tests':
    d.docker('stage-only-c12-tests', 'cp', str(HERE / 'cpjudge/c12_tests.py'), SITE + ':/app/cpjudge/c12_tests.py')
    d.docker('three-native-c12-upload-tests', 'exec', '--user', '1000:1000', SITE, 'python', 'manage.py', 'test',
             'cpjudge.c12_tests.UploadRaceTests', '--settings=dmoj.cpj_integration_settings', '--keepdb', '--noinput', '-v', '2')
elif action == 'browser':
    folder = WORK / 'browser' / d.STAMP
    folder.mkdir(parents=True, mode=0o700)
    d.docker('actual-c12-browser-and-http-concurrency', 'run', '--rm', '--user', f'{os.getuid()}:{os.getgid()}',
             '--network', 'host', '--shm-size', '512m', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
             '--mount', f'type=bind,src={folder},dst=/results',
             '--mount', f'type=bind,src={ROOT / "build/phase-c-checkpoint1-1/accounts.json"},dst=/run/accounts.json,readonly',
             '--mount', f'type=bind,src={WORK / "race.zip"},dst=/run/race.zip,readonly',
             '--mount', f'type=bind,src={HERE / "c12_browser.py"},dst=/tests/browser.py,readonly',
             'cpjudge-b01-browser:local1', 'python', '/tests/browser.py')
    (OUT / 'browser.json').write_text((folder / 'browser.json').read_text())
elif action == 'preserve':
    report = json.loads((OUT / 'browser.json').read_text())
    raw = d.shell('c12-data-history-files-preservation', SNAPSHOT + '\nREPORT=' + repr(report) + '\n' + '''
from django.db import transaction
from judge.models import Profile,ContestParticipation
from cpjudge.models import ImportJob,ProblemVersion,Grant,Audit
before=json.loads(Path('/tmp/c12-before.json').read_text())
# Restore only native ended-contest pointers cleared by normal browser access.
with transaction.atomic():
 for old in before['rows']['judge.profile']:
  p=Profile.objects.select_for_update().get(pk=old['id'])
  if p.current_contest_id==old['current_contest_id']:continue
  assert p.user.username in ('C1LIVEA','C1LIVEB') and p.current_contest_id is None
  previous=ContestParticipation.objects.get(pk=old['current_contest_id'])
  assert previous.user_id==p.pk and previous.ended
  Profile.objects.filter(pk=p.pk).update(current_contest_id=previous.pk)
after=rows();allowed={'auth.user':{'last_login'},'judge.profile':{'last_access','last_ip','ip'},'cpjudge.identity':{'generation'},'judge.judge':{'ping','load','last_ip'}}
models={m._meta.label_lower:m for m in apps.get_models() if not m._meta.proxy}
count=0
for label,oldrows in before['rows'].items():
 if label=='sessions.session':continue
 pk=models[label]._meta.pk.attname
 current={r[pk]:r for r in after[label]}
 for old in oldrows:
  assert old[pk] in current,('removed',label)
  delta={k for k in old if old[k]!=current[old[pk]][k]}
  assert delta<=allowed.get(label,set()),('changed',label,delta)
  count+=1
 new=set(current)-{r[pk] for r in oldrows}
 if label=='cpjudge.importjob':assert new=={REPORT['race_job'],REPORT['other_owner_job']}
 elif label=='cpjudge.grant':
  assert len(new)==1
  grant=next(r for r in after[label] if r[pk] in new)
  g=Grant.objects.select_related('user','contest').get(pk=grant[pk])
  assert g.user.username=='C1LIVEB' and g.contest.key=='c1liveb' and g.capability=='problems.import' and not g.revoked
 elif label=='cpjudge.audit':
  assert len(new)==1
  audit=Audit.objects.select_related('subject').get(pk=next(iter(new)))
  assert audit.subject.username=='C1LIVEB' and audit.action=='grant.create'
 else:assert not new,('unexpected additions',label)
currentfiles=files()
assert all(currentfiles.get(k)==v for k,v in before['files'].items()),'Private files changed'
newfiles=set(currentfiles)-set(before['files'])
expected=set(ImportJob.objects.filter(pk__in=[REPORT['race_job'],REPORT['other_owner_job']]).values_list('archive_key',flat=True))
assert newfiles==expected,('orphans',newfiles-expected)
a=ImportJob.objects.get(pk=24);b=ImportJob.objects.get(pk=REPORT['other_owner_job'])
assert a.owner_id!=b.owner_id and a.package_sha256==b.package_sha256 and a.archive_key!=b.archive_key
assert (a.attempt,a.status)==(REPORT['attempt'],'succeeded')
assert ProblemVersion.objects.get(job=a,attempt=a.attempt).code==REPORT['native_code']
print('C12_RESULT='+json.dumps({'status':'PASS','models_checked':len(models),'existing_rows_checked':count,'old_private_files_unchanged':len(before['files']),'new_archives':len(newfiles),'orphan_new_files':0,'existing_job_version_attempt_audit_history_unchanged':True,'accounts_passwords_results_preserved':True,'normal_login_access_generation_and_liveness_only':True,'ended_native_contest_pointers_restored':True}))
''')
    result = json.loads(raw.decode().split('C12_RESULT=', 1)[1].splitlines()[0])
    baseline = json.loads((WORK / 'containers.json').read_text())
    for name, digest in baseline.items():
        obj = json.loads(d.docker('preserve-container-' + name, 'inspect', name))[0]
        assert hashlib.sha256(json.dumps({k: obj[k] for k in ('Id', 'Image', 'Config', 'HostConfig', 'Mounts')}, sort_keys=True).encode()).hexdigest() == digest
    result['container_identity_configuration_preserved'] = True
    (OUT / 'preservation.json').write_text(json.dumps(result, indent=2) + '\n')
else:
    raise SystemExit('Unknown C12 action')
