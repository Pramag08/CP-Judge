import re,json
from pathlib import Path
from judge.models import Submission,ContestParticipation
print('task_submissions',list(Submission.objects.filter(problem__code='pv900000000000000002').values('id','status','result')))
print('entries',list(ContestParticipation.objects.filter(contest__key='cintlocal1').values('id','user_id','virtual')))
p=Path('/tmp/c07-http.log')
if p.exists():
 rows=[]
 for line in p.read_text(errors='replace').splitlines():
  m=re.search(r'"(GET|POST) ([^ ]+) HTTP[^\"]*" ([0-9]+)',line)
  if m and ('/problem/pv900000000000000002' in m[2] or '/contest/cintlocal1' in m[2]):rows.append((m[1],m[2],m[3]))
 print('recent_relevant_http',rows[-12:])
