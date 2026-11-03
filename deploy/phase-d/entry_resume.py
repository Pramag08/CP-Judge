"""Preserve the completed browser pre-start assertions; isolate reused-version access."""
import json
from pathlib import Path
from judge.models import Contest
from cpjudge.models import ContestEntry,Audit
from cpjudge.entries import sanction
old=Contest.objects.get(key='d07local1');c=Contest.objects.get(key='d07local2')
entry=ContestEntry.objects.get(contest=old,user_id=2)
if entry.status=='active':sanction(old.workflow.owner,old.key,entry.pk,'remove','Close only the expired task-owned first browser fixture entry; isolate reused immutable-version access.')
# The browser stopped at its pre-start direct-problem assertion, AFTER each of
# these actions/assertions completed. Cross-check durable audits before resuming.
new=ContestEntry.objects.get(contest=c,user_id=2)
registrations=Audit.objects.filter(scope=str(c.pk),subject_id=2,action='entry.register')
withdrawals=Audit.objects.filter(scope=str(c.pk),subject_id=2,action='entry.withdraw')
assert registrations.count()==2 and withdrawals.count()==1
assert not registrations.filter(created__gte=c.start_time).exists() and not withdrawals.filter(created__gte=c.start_time).exists()
assert new.status=='active'
checkpoint={'status':'RUNNING','contest':c.key,'checks':{'browser_prestart_register_withdraw_reregister_idempotent_native_leave_csrf_author_conflict':True},'resume_note':'Prior browser stopped after completed pre-start assertions; exact pre-start registration/withdrawal audits checked. Reused-version access isolated by audited removal from task-owned expired first fixture.'}
Path('/tmp/d07-browser-checkpoint.json').write_text(json.dumps(checkpoint,indent=2))
print('Prior pre-start browser actions verified against exact audits; only expired task-owned entry removed with reason. Ready to resume late entry and actual submission.')
