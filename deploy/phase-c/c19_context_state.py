import json
from pathlib import Path
from judge.models import Profile,ContestParticipation
before=json.loads(Path('/tmp/c13-identity-before.json').read_text())
for old in before['judge.profile']:
 p=Profile.objects.get(pk=old['id'])
 if p.current_contest_id!=old['current_contest_id']:
  c=p.current_contest
  print({'profile_id':p.pk,'old':old['current_contest_id'],'current':p.current_contest_id,'current_virtual':c.virtual if c else None,'current_contest_end':str(c.contest.end_time) if c else None,'current_ended':c.ended if c else None,'current_owner':c.user_id if c else None})
