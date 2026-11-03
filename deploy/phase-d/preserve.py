import json
from pathlib import Path
from django.apps import apps
from cpjudge.models import ContestWorkflow,ContestVersionAdmission
from cpjudge.publication import verify_native
from cpjudge.admission import verify_approval
from judge.models import Contest,Judge
before=json.loads(Path('/tmp/d01-before.json').read_text())
allowed={'auth.user':{'last_login'},'judge.profile':{'last_access','ip'},'judge.judge':{'ping','load','last_ip','start_time'},'cpjudge.identity':{'generation'}}
issues=[];count=0
for label,oldrows in before.items():
 if label=='sessions.session':continue
 if label=='judge.runtimeversion':
  # Native authentication deletes/recreates advertisements; compare exact content.
  current=list(apps.get_model(label).objects.all().values())
  semantic=lambda rs:sorted(json.dumps({k:v for k,v in r.items() if k!='id'},sort_keys=True) for r in rs)
  assert semantic(oldrows)==semantic(current),'Runtime advertisement content changed'
  count+=len(oldrows);continue
 model=apps.get_model(label);pk=model._meta.pk.attname
 rows={r[pk]:r for r in json.loads(json.dumps(list(model.objects.all().values()),default=str))}
 for old in oldrows:
  assert old[pk] in rows,'Removed old row: '+label
  delta={k for k in old if old[k]!=rows[old[pk]][k]}
  if not delta<=allowed.get(label,set()):issues.append((label,old[pk],sorted(delta)))
  count+=1
assert not issues,issues
c=Contest.objects.get(key='d01local1');assert c.is_visible
assert c.workflow.display_timezone=='Asia/Kolkata' and c.workflow.eligibility=='provisioned'
assert c.start_time.hour==4 and c.start_time.minute==30 and c.end_time.hour==6 and c.end_time.minute==30
cp=c.contest_problems.get();assert cp.order==2 and cp.workflow_label.label=='Q'
assert cp.points==1 and not cp.partial and not cp.is_pretested
assert not cp.problem.is_public and c.time_limit is None
assert verify_native(ContestVersionAdmission.objects.get(contest_problem=cp).version)
assert verify_approval(ContestVersionAdmission.objects.get(contest_problem=cp))
assert Judge.objects.get(name='cpjudge-local-worker').online
assert c.get_label_for_problem(0)=='Q'
result={'status':'PASS','existing_non_session_rows':count,'model_sets':len(before),'original_accounts_hashes_submissions_imports_audits_contests_preserved':True,
 'allowed_differences':'login/access/session-generation and judge liveness only','new_contest':c.key,'native_label':'Q','native_order':2,
 'timezone':c.workflow.display_timezone,'utc_start_hour_minute':[4,30],'utc_end_hour_minute':[6,30],
 'native_limits':[cp.problem.time_limit,cp.problem.memory_limit],'version_still_private':True,'no_new_judging':True}
p=Path('/tmp/d01-preservation.json');p.write_text(json.dumps(result,indent=2));print('Preserved all baseline non-session rows; published rules/label/order/timezone/private version verified.')
