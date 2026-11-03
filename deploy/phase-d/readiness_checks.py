"""Actual read-only publication channel freshness and authentication negatives."""
import json,secrets,time
from pathlib import Path
from cpjudge import readiness_wire as wire
from cpjudge.contest_readiness import check
from cpjudge.bridge_readiness import CONFIG
from judge.models import Judge,Contest
from cpjudge.models import ContestVersionAdmission
c=Contest.objects.get(key='d01local1');a=ContestVersionAdmission.objects.get(contest_problem__contest=c)
config=json.loads(CONFIG.read_text());worker=Judge.objects.get(name=config['worker_name'])
check(a.version.code,a.runtime.key)
base=dict(schema=1,code=a.version.code,language=a.runtime.key,nonce=secrets.token_hex(32),issued=time.time())
checks={}
for name,body,key in [('stale',dict(base,issued=time.time()-60),worker.auth_key),('wrong_auth',base,'synthetic-invalid-key'),('missing_problem',dict(base,code='pv999999999999999999'),worker.auth_key)]:
 try:wire.request(body,key,address=('127.0.0.1',9995))
 except Exception:checks[name]=True
 else:raise AssertionError('Invalid readiness challenge accepted: '+name)
result={'status':'PASS','actual_fresh_worker_challenge':True,'actual_stale_challenge_rejected':checks['stale'],
 'actual_wrong_auth_rejected':checks['wrong_auth'],'actual_missing_problem_rejected':checks['missing_problem'],
 'mutated_data_or_worker_configuration':False}
Path('/tmp/d01-readiness-checks.json').write_text(json.dumps(result,indent=2))
print('PASS: actual fresh worker readiness; stale/authentication/missing-problem challenges fail closed.')
