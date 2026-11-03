"""Independently verify the one admitted native execution; never resubmit."""
from judge.models import Submission
from cpjudge.models import ContestReceipt
from cpjudge.entries import validate_receipt
s=Submission.objects.get(pk=23)
assert s.contest_object.key=='d07local2'
r=ContestReceipt.objects.get(submission=s)
assert validate_receipt(s)
print('Native execution:',s.pk,s.status,s.result,'cases',s.test_cases.count(),'source CR/LF',s.source.source.count('\r'),s.source.source.count('\n'))
assert s.status=='D' and s.result=='AC' and s.case_total==s.case_points==3
assert s.test_cases.count()==3 and not s.test_cases.exclude(status='AC',points=1,total=1).exists()
print('All three actual case records agree with the durable native receipt.')
