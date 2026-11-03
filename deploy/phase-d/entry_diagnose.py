import json
from pathlib import Path
from judge.models import Submission,Contest
from cpjudge.models import ContestReceipt
c=Contest.objects.get(key='d07local1')
print('Task submission state:',list(Submission.objects.filter(contest_object=c).values('id','status','result')))
receipts=list(ContestReceipt.objects.filter(entry__contest=c).values('submission_id','request_key'))
if receipts:
 p=Path('/tmp/d07-recovered-submission.json');p.write_text(json.dumps({'id':receipts[0]['submission_id'],'key':receipts[0]['request_key']}));p.chmod(0o600)
print('Durable receipts:',len(receipts))
print(Path('/tmp/c07-http.log').read_text()[-4200:])
