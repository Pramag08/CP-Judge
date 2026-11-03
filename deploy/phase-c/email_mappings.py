"""Local private four-account mapping worksheet; never enables email-only login."""
import argparse,gzip,json,os,stat,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
WORK=ROOT/'build/email-mappings-1'
IDS={1:'b01-staff',2:'b01-participant',7:'b10tmpa',8:'b10tmpb'}

def development_assignment(row):
 return (row.get('assignment_kind')=='organizer_assigned_development' and row.get('organizer_assigned') is True
         and row.get('verified_by_organizer') is False and row.get('mailbox_verified') is False
         and row.get('real_participant_identity') is False)

def authorized_assignment(row):
 if row.get('assignment_kind')=='organizer_assigned_development':return development_assignment(row)
 return row.get('assignment_kind') is None and row.get('verified_by_organizer') is True

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('action',choices=['prepare','check','apply'])
 p.add_argument('--file',type=Path,default=WORK/'mappings.json')
 p.add_argument('--actor-id',type=int,default=1)
 o=p.parse_args();WORK.mkdir(mode=0o700,parents=True,exist_ok=True);WORK.chmod(0o700)
 path=o.file.absolute()
 if o.action=='prepare':
  fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
  with os.fdopen(fd,'w') as f:json.dump({'accounts':[{'user_id':pk,'username':name,'email':'','verified_by_organizer':False,'reason':''} for pk,name in IDS.items()]},f,indent=2);f.write('\n')
  print('Blank private worksheet created: '+str(path));return
 if path.is_symlink() or path.stat().st_uid!=os.getuid() or stat.S_IMODE(path.stat().st_mode)!=0o600:
  raise SystemExit('Mapping file must be owned by you, not a symlink, and mode0600.')
 data=json.loads(path.read_text());rows=data.get('accounts',[])
 if len(rows)!=4 or {r.get('user_id'):r.get('username') for r in rows}!=IDS:raise SystemExit('Keep the four original account IDs/usernames unchanged.')
 missing=sum(not r.get('email','').strip() or not authorized_assignment(r) or not r.get('reason','').strip() for r in rows)
 if missing:raise SystemExit(f'{missing} rows still need a verified or explicitly organizer-assigned development address, accurate provenance and audit reason. Database/login/passwords unchanged.')
 payload=json.dumps({'actor_id':o.actor_id,'accounts':rows,'apply':o.action=='apply'})
 # Reuse the same Docker-group entry as the local manager. Private addresses are
 # stdin only; never command arguments, stdout or the command ledger.
 remote='''import json,sys
from pathlib import Path
p=Path('/tmp/cpj-email-mappings-input.json');p.write_bytes(sys.stdin.buffer.read());p.chmod(0o600)
'''
 def docker(args,stdin=None):
  import shlex
  proc=subprocess.run(['sg','docker','-c',shlex.join(['docker',*args])],input=stdin,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
  log=WORK/'last-operation.log';log.write_bytes(proc.stdout);log.chmod(0o600)
  if proc.returncode:raise SystemExit('Operation rejected. Inspect the private last-operation.log; no addresses printed.')
  return proc.stdout
 docker(['exec','-i','cpjudge-b01-site','python','-c',remote],payload.encode())
 if o.action=='apply':
  import datetime
  stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
  raw=docker(['exec','cpjudge-b01-db','sh','-c','exec mariadb-dump --user=root --password="$MARIADB_ROOT_PASSWORD" --single-transaction --routines --events --databases b01'])
  backup=WORK/(stamp+'-database.sql.gz')
  with backup.open('xb') as f:os.chmod(backup,0o600);f.write(gzip.compress(raw))
  assert gzip.decompress(backup.read_bytes())==raw and b'-- Dump completed on' in raw
 code='''import json
from pathlib import Path
from django.db import transaction
from django.contrib.auth import get_user_model
from cpjudge.email_identity import canonical_email,correct_email,email_only,lock_policy
from cpjudge.identity import require_admin
from cpjudge.models import Identity
from django.core.exceptions import ValidationError
from django.db import IntegrityError
payload=json.loads(Path('/tmp/cpj-email-mappings-input.json').read_text());U=get_user_model()
try:
 with transaction.atomic():
  actor=U.objects.get(pk=payload['actor_id']);require_admin(actor);lock_policy()
  if email_only():raise ValidationError('This worksheet is for transitional mode only.')
  keys=[canonical_email(r['email']) for r in payload['accounts']]
  if len(set(keys))!=4:raise ValidationError('Duplicate worksheet addresses.')
  for row,key in zip(payload['accounts'],keys):
   user=U.objects.select_for_update().get(pk=row['user_id'],username=row['username'])
   if user.email.strip():raise ValidationError('An existing address was filled since this worksheet was created; re-inventory.')
   if Identity.objects.filter(canonical_email=key).exclude(user=user).exists():raise ValidationError('Address already assigned.')
   # Also inspect native addresses belonging to unstaged accounts.
   for other in U.objects.exclude(pk=user.pk):
    try:existing=canonical_email(other.email)
    except ValidationError:continue
    if existing==key:raise ValidationError('Address already present in native accounts.')
  if payload['apply']:
   old={u.pk:u.password for u in U.objects.all()}
   for row in payload['accounts']:
    correct_email(actor,row['user_id'],row['email'],row['reason'],assignment_kind=row.get('assignment_kind'))
   assert all(U.objects.get(pk=pk).password==password for pk,password in old.items())
   assert not email_only()
except (ValidationError,IntegrityError,U.DoesNotExist):
 raise RuntimeError('Mapping validation rejected; inspect IDs/verified values privately. No partial mapping or password change.') from None
print('Four mappings validated'+(' and atomically applied' if payload['apply'] else ' without DB changes')+'. Passwords preserved; legacy login remains enabled.')
'''
 raw=docker(['exec','-i','cpjudge-b01-site','python','manage.py','shell'],code.encode())
 print('Four authorized mappings '+('applied' if o.action=='apply' else 'validated')+'. Passwords preserved; legacy login stays enabled. No email-only cutover performed.')

if __name__=='__main__':main()
