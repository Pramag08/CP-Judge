import json
from pathlib import Path
from judge.models import Submission,ContestSubmission,ContestProblem
from cpjudge.models import ProblemProbe,ProblemVersion
from cpjudge.probes import binding
from cpjudge.publication import verify_native
v=ProblemVersion.objects.get(pk=2);assert verify_native(v)
assert not v.problem.is_public and not v.problem.allowed_languages.exists() and not ContestProblem.objects.filter(problem=v.problem).exists()
probes=list(ProblemProbe.objects.filter(version=v).order_by('pk'))
assert len(probes)==2
trace=[json.loads(x) for x in Path('/tmp/c11-native-trace.jsonl').read_text().splitlines()]
rows=[]
for probe,verdict in zip(probes,('AC','WA')):
 assert binding(probe);s=probe.execution;assert s.status=='D' and s.result==verdict
 cases=list(s.test_cases.all());assert len(cases)==3 and all(c.status==verdict for c in cases)
 assert s.contest_object_id is None and not ContestSubmission.objects.filter(submission=s).exists()
 packets=[r for r in trace if r.get('submission-id')==s.pk and r['direction']=='sent' and r['name']=='submission-request']
 assert len(packets)==1 and packets[0]['time-limit']==0.5 and packets[0]['memory-limit']==65536 and packets[0]['language']=='CPP17'
 callbacks=[c for r in trace if r.get('submission-id')==s.pk and r['direction']=='received-and-handled' and r['name']=='test-case-status' for c in r['cases']]
 assert len(callbacks)==3
 rows.append({'probe':probe.pk,'execution_id':s.pk,'verdict':s.result,'cases':3,'callback_cases':3,'native_packets':1,'runtime':'CPP17','time_seconds':0.5,'memory_kib':65536})
before=json.loads(Path('/tmp/c13-identity-before.json').read_text())
for label in ('judge.submission','judge.submissionsource','judge.submissiontestcase','judge.contestsubmission','judge.contestparticipation','judge.contestproblem'):
 from django.apps import apps
 m=apps.get_model(label);pk=m._meta.pk.attname;current={r[pk]:r for r in json.loads(json.dumps(list(m.objects.all().values()),default=str))}
 assert all(current.get(r[pk])==r for r in before[label]),('changed prior results',label)
Path('/tmp/c13-proof.json').write_text(json.dumps({'status':'PASS','runs':rows,'prior_results_standings_unchanged':True,'private_and_submission_disabled':True}));Path('/tmp/c13-proof.json').chmod(0o600)
print('Actual probe SQL/callback/native-packet agreement and historical results preservation passed.')
