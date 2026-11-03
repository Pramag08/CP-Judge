"""Run inside contest_journey coordinator; idle guarded code update, no verdict edits."""
# Existing local helpers stop an idle worker first, then bridge/Celery/events.
import hashlib
os.environ['CPJ_SITE_REPORT_DIR']=str(OUT)
run('idle-worker-stop',[sys.executable,'-B',str(HERE/'b03.py'),'stop'])
run('idle-services-stop',[sys.executable,'-B',str(HERE/'b02.py'),'stop'])
docker('copy-fixed-format','cp',str(ROOT/'patches/site/contest-format/cpjudge_icpc.py'),SITE+':/app/judge/contest_format/cpjudge_icpc.py')
patch=r'''
import hashlib,json
from pathlib import Path
root=Path('/app')
changes={}
p=root/'judge/contest_format/__init__.py';text=p.read_text()
line='from judge.contest_format.cpjudge_icpc import CPJudgeICPCFormat\n'
if line not in text:p.write_text(text+line)
changes[str(p)]={'before':hashlib.sha256(text.encode()).hexdigest(),'after':hashlib.sha256(p.read_bytes()).hexdigest()}
p=root/'judge/views/contests.py';text=p.read_text()
old="""    return base_contest_ranking_list(contest, problems, contest.users.filter(virtual=0)
                                     .prefetch_related('user__organizations')
                                     .annotate(submission_cnt=Count('submission'))
                                     .order_by('is_disqualified', '-score', 'cumtime', 'tiebreaker', '-submission_cnt'))"""
new="""    if contest.format_name == 'cpjudge_icpc_v1':
        return base_contest_ranking_list(contest, problems, contest.users.filter(virtual=0, is_disqualified=False)
                                        .prefetch_related('user__organizations').order_by('-score', 'cumtime', 'id'))
"""+old
if "if contest.format_name == 'cpjudge_icpc_v1':" not in text:
 assert text.count(old)==1;p.write_text(text.replace(old,new))
changes[str(p)]={'before':hashlib.sha256(text.encode()).hexdigest(),'after':hashlib.sha256(p.read_bytes()).hexdigest()}
p=root/'judge/models/submission.py';text=p.read_text()
old="""        contest.points = round(self.case_points / self.case_total * contest_problem.points
                               if self.case_total > 0 else 0, 3)
        if not contest_problem.partial and contest.points != contest_problem.points:
            contest.points = 0"""
new="""        if contest.participation.contest.format_name == 'cpjudge_icpc_v1':
            from judge.contest_format.cpjudge_icpc import full_ac
            contest.points = int(full_ac(self.status, self.result, self.case_points, self.case_total))
        else:
"""+'\n'.join('    '+line for line in old.splitlines())
if "from judge.contest_format.cpjudge_icpc import full_ac" not in text:
 assert text.count(old)==1;p.write_text(text.replace(old,new))
changes[str(p)]={'before':hashlib.sha256(text.encode()).hexdigest(),'after':hashlib.sha256(p.read_bytes()).hexdigest()}
# Additive metadata-only choice migration; native varchar schema remains unchanged.
from judge.contest_format.registry import choices
# This shell imported the old registry before patching; import the new module explicitly.
import judge.contest_format.cpjudge_icpc
migration=root/'judge/migrations/0154_cpjudge_icpc_choice.py'
content="from django.db import migrations, models\n\nclass Migration(migrations.Migration):\n    dependencies = [('judge', '0153_reconcile_model_metadata')]\n    operations = [migrations.AlterField(model_name='contest', name='format_name', field=models.CharField(choices="+repr(choices())+", default='default', help_text='The contest format module to use.', max_length=32, verbose_name='contest format'))]\n"
if migration.exists():assert migration.read_text()==content
else:migration.write_text(content)
for p in (root/'judge/contest_format/cpjudge_icpc.py',root/'judge/views/contests.py',root/'judge/models/submission.py',migration):compile(p.read_text(),str(p),'exec')
print('JOURNEY_RESULT='+json.dumps({'status':'PASS','source_changes':changes,'migration':'0154_cpjudge_icpc_choice'}))
'''
result=shell('bounded-native-scoring-patch',patch)
docker('copy-metadata-migration','cp',SITE+':/app/judge/migrations/0154_cpjudge_icpc_choice.py',str(HERE/'migrations/0154_cpjudge_icpc_choice.py'))
docker('additive-choice-migration','exec',SITE,'python','manage.py','migrate','judge','0154','--noinput')
# Only now select the new format on the task-owned contest and recompute native scores.
result['recompute']=shell('select-preset-and-recompute',"import json\nfrom judge.models import Contest,Submission\nc=Contest.objects.get(key='b10b11local1')\nassert not Submission.objects.filter(status__in=Submission.IN_PROGRESS_GRADING_STATUS).exists()\nc.format_name='cpjudge_icpc_v1';c.format_config={'penalty':20};c.full_clean();c.save(update_fields=['format_name','format_config'])\nfor p in c.users.all():p.recompute_results()\nprint('JOURNEY_RESULT='+json.dumps({'contest':c.key,'recomputed':c.users.count(),'no_rejudge':True}))")
# Web imports registry/models at startup; native bridge also needs the new format.
docker('reload-web-code','exec','-i',SITE,'python',stdin="import os,signal\nfrom pathlib import Path\nfor p in Path('/proc').iterdir():\n if not p.name.isdigit():continue\n try:a=(p/'cmdline').read_bytes().split(bytes([0]))\n except OSError:continue\n if a[1:3]==[b'manage.py',b'runserver']:os.kill(int(p.name),signal.SIGTERM)\n")
docker('start-updated-web','exec','-d',SITE,'sh','-c','exec python manage.py runserver 0.0.0.0:8000 --noreload > /tmp/b11-http.log 2>&1')
run('managed-start-after-code-update',[sys.executable,'-B',str(HERE/'manage.py'),'start'])
docker('migration-consistency','exec',SITE,'python','manage.py','makemigrations','--check','--dry-run')
save('scoring-install.json',result)
