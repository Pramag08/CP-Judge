"""C10 focused validation/activation; all subprocess output stays private."""
import hashlib,json,os,sys,gzip
from pathlib import Path
import c05 as d
ROOT=d.ROOT;HERE=d.HERE;SITE=d.SITE
WORK=ROOT/'build/phase-c-c10-1';OUT=ROOT/'reports/phase-c-c10-1'
WORK.mkdir(mode=0o700,parents=True,exist_ok=True);WORK.chmod(0o700);OUT.mkdir(parents=True,exist_ok=True)
d.WORK=WORK;d.OUT=OUT

def snapshot():
 assert not (OUT/'containers-before.json').exists(), 'Snapshot exists; inspect rather than replace the baseline'
 d.shell('snapshot-existing-rows', '''import json
from pathlib import Path
from django.apps import apps
from judge.models import Submission
assert not Submission.objects.filter(status__in=Submission.IN_PROGRESS_GRADING_STATUS).exists()
p=Path('/tmp/c10-before.json');assert not p.exists()
p.write_text(json.dumps({m._meta.label_lower:list(m.objects.all().values()) for m in apps.get_models() if not m._meta.proxy},default=str));p.chmod(0o600)
print('C10 private snapshot retained.')
''')
 data={}
 for name in (SITE,'cpjudge-b03-worker','cpjudge-b01-db','cpjudge-b01-redis'):
  obj=json.loads(d.docker('snapshot-container-'+name,'inspect',name))[0]
  data[name]={'id':obj['Id'],'image':obj['Image'],'started':obj['State']['StartedAt'],'config_hash':hashlib.sha256(json.dumps({k:obj[k] for k in ('Config','HostConfig','Mounts')},sort_keys=True).encode()).hexdigest()}
 (OUT/'containers-before.json').write_text(json.dumps(data,indent=2)+'\n')

def stage():
 for name in ('models.py','sessions.py','publication.py','native.py','urls.py','views.py','c10_tests.py'):
  d.docker('stage-'+name,'cp',str(HERE/'cpjudge'/name),SITE+':/app/cpjudge/'+name)
 for name in ('import_confirm.html','publication_error.html'):
  d.docker('stage-'+name,'cp',str(HERE/'cpjudge/templates/cpjudge'/name),SITE+':/app/cpjudge/templates/cpjudge/'+name)
 d.docker('stage-recovery-command','cp',str(HERE/'cpjudge/management/commands/recover_publications.py'),SITE+':/app/cpjudge/management/commands/recover_publications.py')
 d.docker('ensure-tools-module-directory','exec',SITE,'mkdir','-p','/app/tools')
 for name in ('site_problem.py','verify_install.py'):
  d.docker('stage-native-installer-'+name,'cp',str(ROOT/'tools'/name),SITE+':/app/tools/'+name)
 for name,path in (('package',ROOT/'build/phase-c-c07-1/package.zip'),('groups',ROOT/'build/phase-c-1/synthetic/groups.zip')):
  d.docker('stage-synthetic-test-fixture-'+name,'cp',str(path),SITE+':/tmp/c10-'+name+'.zip')
 d.docker('stage-native-renderer','cp',str(ROOT/'deploy/site-local/imported_statement_filter.py'),SITE+':/app/judge/jinja2/imported_statement.py')
 d.docker('stage-native-template-extension','cp',str(HERE/'c10_overlay.py'),SITE+':/tmp/c10_overlay.py')
 d.docker('apply-native-template-extension','exec',SITE,'python','/tmp/c10_overlay.py')

if __name__=='__main__':
 action=sys.argv[1]
 if action=='backup':
  assert not (WORK/'backup.json').exists(),'Inspect existing backup; do not replace'
  snapshot()
  raw=d.docker('private-database-backup','exec','cpjudge-b01-db','sh','-c','exec mariadb-dump --user=root --password="$MARIADB_ROOT_PASSWORD" --single-transaction --routines --events --databases b01')
  path=WORK/(d.STAMP+'-database.sql.gz')
  with path.open('xb') as f:os.chmod(path,0o600);f.write(gzip.compress(raw))
  assert gzip.decompress(path.read_bytes())==raw and b'-- Dump completed on' in raw
  (WORK/'backup.json').write_text(json.dumps({'path':str(path.relative_to(ROOT)),'full_gzip_readback':True,'restore_tested':False}));(WORK/'backup.json').chmod(0o600)
 elif action=='stage':stage()
 elif action=='migration':
  assert (WORK/'backup.json').exists()
  d.docker('generate-additive-version-migration','exec','--user','1000:1000',SITE,'python','manage.py','makemigrations','cpjudge','--noinput')
  d.docker('retain-version-migration','cp',SITE+':/app/cpjudge/migrations/.',str(HERE/'cpjudge/migrations'))
  d.docker('apply-version-migration','exec',SITE,'python','manage.py','migrate','--noinput')
 elif action=='tests':
  d.docker('focused-c10-publication-and-c09-regressions','exec','--user','1000:1000',SITE,'python','manage.py','test','cpjudge.c10_tests.PublicationTests','cpjudge.integration_tests.NativeIntegrationTests.test_ajax_shortcircuit_and_sources_use_current_session_and_scope','cpjudge.integration_tests.NativeIntegrationTests.test_events_anonymous_cross_scope_and_replaced_session','cpjudge.c09_tests.StatementTests.test_render_sample_lines_math_asset_headers_and_no_raw_data','cpjudge.c09_tests.StatementTests.test_removals_reported_and_no_css_urls_events_or_active_dom','cpjudge.c09_tests.StatementTests.test_logged_out_participant_unrelated_author_and_revocation_asset_denials','--settings=dmoj.cpj_integration_settings','--keepdb','--noinput','-v','2')
 elif action=='activate':
  d.shell('guard-idle-before-code-reload',"from judge.models import Submission\nfrom cpjudge.models import ImportJob\nassert not Submission.objects.filter(status__in=Submission.IN_PROGRESS_GRADING_STATUS).exists()\nassert not ImportJob.objects.filter(status__in=('queued','running')).exclude(archive_key__startswith='c08-state-').exclude(archive_key__startswith='c09-state-').exists()\nprint('No active judging or actual conversion job.')")
  source=(HERE/'c07_activate.py').read_text();body=source.split("data=b\'\'\'",1)[1].split("\'\'\')",1)[0]
  d.docker('reload-only-http-celery','exec','-i',SITE,'python',data=body.encode())
 elif action=='grant-fixture':
  d.shell('grant-only-scoped-c10-publication-fixture',"""from django.contrib.auth import get_user_model
from judge.models import Contest
from cpjudge.policy import grant_scope
u=get_user_model();actor=u.objects.filter(is_active=True,is_superuser=True).exclude(username='C1LIVEADMIN').order_by('pk').first()
grant_scope(actor,u.objects.get(username='C1LIVEA'),Contest.objects.get(key='c1livea'),'problems.publish')
print('C10 author fixture has explicit publication scope.')
""")
 elif action=='browser':
  folder=WORK/'browser'/d.STAMP;folder.mkdir(mode=0o700,parents=True)
  d.docker('actual-c10-browser-publication','run','--rm','--user',f'{os.getuid()}:{os.getgid()}','--network','host','--shm-size','512m','--cap-drop','ALL','--security-opt','no-new-privileges',
   '--mount',f'type=bind,src={folder},dst=/results',
   '--mount',f'type=bind,src={ROOT/"build/phase-c-checkpoint1-1/accounts.json"},dst=/run/accounts.json,readonly',
   '--mount',f'type=bind,src={HERE/"c10_browser.py"},dst=/tests/browser.py,readonly',
   'cpjudge-b01-browser:local1','python','/tests/browser.py')
  (OUT/'browser.json').write_text((folder/'browser.json').read_text())
 elif action=='verify-publication':
  data=json.loads((OUT/'browser.json').read_text())
  raw=d.shell('verify-published-native-and-installed-files','CODE='+repr(data['native_code'])+'\n'+"""import json
from cpjudge.models import ProblemVersion
from cpjudge.publication import verify_native,destination
from judge.models import ContestProblem,Submission
v=ProblemVersion.objects.select_related('problem','job__contest').get(code=CODE)
assert verify_native(v)
p=v.problem;m=v.manifest
assert not p.is_public and p.is_manually_managed and not p.allowed_languages.exists()
assert not ContestProblem.objects.filter(problem=p).exists()
assert not Submission.objects.filter(problem=p).exists()
print('C10_NATIVE='+json.dumps({'status':'PASS','version_id':v.pk,'job_id':v.job_id,'code':v.code,'state':v.state,'time_seconds':p.time_limit,'memory_kib':p.memory_limit,'points':p.points,'checker_executor':m['checker']['args']['lang'],'test_groups_or_cases':len(m['test_cases']),'samples':m['samples'],'all_installed_file_hashes_and_native_fields_agree':True,'is_public':p.is_public,'contest_assigned':False,'submission_languages':[],'submissions':0,'coordinator_private_only':str(destination(v)).startswith('/app/private-cpj-imports/publications/'),'worker_readiness':'NOT TESTED','judging':'NOT RUN'}))
""")
  result=json.loads(raw.decode().split('C10_NATIVE=',1)[1].splitlines()[0]);(OUT/'native-files.json').write_text(json.dumps(result,indent=2)+'\n')
  d.docker('migration-consistency','exec',SITE,'python','manage.py','makemigrations','--check','--dry-run')
 elif action=='restore-browser-context':
  raw=d.shell('restore-only-native-expired-browser-contest-context',"""import json
from pathlib import Path
from judge.models import Profile,ContestParticipation
from django.db import transaction
before=json.loads(Path('/tmp/c10-before.json').read_text())['judge.profile']
restored=[];pk=Profile._meta.pk.attname
with transaction.atomic():
 for old in before:
  profile=Profile.objects.select_for_update().select_related('user').get(pk=old[pk])
  if profile.current_contest_id==old['current_contest_id']:continue
  assert profile.user.username in ('C1LIVEA','C1LIVEB','C1LIVEP')
  assert profile.current_contest_id is None and old['current_contest_id'] is not None
  participation=ContestParticipation.objects.get(pk=old['current_contest_id'])
  assert participation.user_id==profile.pk and participation.ended
  Profile.objects.filter(pk=profile.pk,current_contest_id=None).update(current_contest_id=old['current_contest_id'])
  restored.append({'profile_id':profile.pk,'expired_participation_id':participation.pk,'baseline_pointer_restored':True})
print('C10_CONTEXT='+json.dumps({'status':'PASS','cause':'Native ContestMiddleware/Profile.update_contest clears an ended current contest on authenticated requests','restored':restored,'other_fields_written':False}))
""")
  result=json.loads(raw.decode().split('C10_CONTEXT=',1)[1].splitlines()[0]);(OUT/'browser-context.json').write_text(json.dumps(result,indent=2)+'\n')
 elif action=='preserve':
  source=(HERE/'c07_activate.py').read_text();body=source.split('raw=d.shell(\'preexisting-live-rows-preserved\',"""',1)[1].split('""")',1)[0].replace('/tmp/c07-before.json','/tmp/c10-before.json').replace('C07_PRESERVATION','C10_PRESERVATION')
  raw=d.shell('preserve-existing-rows',body)
  result=json.loads(raw.decode().split('C10_PRESERVATION=',1)[1].splitlines()[0]);(OUT/'preservation.json').write_text(json.dumps(result,indent=2)+'\n')
  before=json.loads((OUT/'containers-before.json').read_text())
  for name,baseline in before.items():
   obj=json.loads(d.docker('verify-container-'+name,'inspect',name))[0]
   current={'id':obj['Id'],'image':obj['Image'],'started':obj['State']['StartedAt'],'config_hash':hashlib.sha256(json.dumps({k:obj[k] for k in ('Config','HostConfig','Mounts')},sort_keys=True).encode()).hexdigest()}
   assert current==baseline
  (OUT/'containers-preserved.json').write_text(json.dumps({'status':'PASS','container_ids_images_configuration_start_times_unchanged':True},indent=2)+'\n')
 else:raise SystemExit('Unknown C10 action')
