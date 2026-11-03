"""One C11 browser submission: mismatch -> pending -> reconnect -> ready -> AC.

Never modifies installed problem bytes, account credentials or published versions.
"""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time

import c11 as env
from c11 import d, WORK, OUT, ROOT, HERE, SITE, WORKER


def enrollment(value):
    d.docker('write-private-enrollment-atomically','exec','-i',SITE,'python','-c',
        "import os,sys;from pathlib import Path;p=Path('/app/cpj-readiness.json');t=p.with_suffix('.next');t.write_bytes(sys.stdin.buffer.read());t.chmod(0o600);os.replace(t,p)",
        data=json.dumps(value).encode())


def state(sid, label):
    raw=d.shell(label,"SID="+str(sid)+"\n"+"""import json
from judge.models import Submission,Judge
s=Submission.objects.get(pk=SID)
print('C11_STATE='+json.dumps({'id':s.pk,'status':s.status,'result':s.result,'case_count':s.test_cases.count(),
 'error':s.error,'worker_online':Judge.objects.get(name='cpjudge-local-worker').online}))
""")
    return json.loads(raw.decode().split('C11_STATE=',1)[1].splitlines()[0])


def assert_pending(sid,label,online=True):
    data=state(sid,label)
    assert data['status']=='QU' and data['result'] is None and data['case_count']==0,data
    assert data['error'].startswith('Waiting for verified problem data'),data
    assert data['worker_online']==online,data
    raw=d.docker('assert-no-packet-'+label,'exec',SITE,'python','-c',
        "import json,sys;from pathlib import Path;p=Path('/tmp/c11-native-trace.jsonl');rows=[json.loads(l) for l in p.read_text().splitlines()] if p.exists() else [];assert not any(r.get('name')=='submission-request' and r.get('submission-id')==int(sys.argv[1]) for r in rows);print('No native dispatch packet for pending submission.')",str(sid))
    return {k:v for k,v in data.items() if k!='error'}


def run():
    assert not (OUT/'live.json').exists(),'Completed live proof already exists; do not resubmit'
    folder=WORK/'browser';folder.mkdir(mode=0o700,exist_ok=True)
    # A previous failed browser after admission must be resumed, never resubmitted.
    assert not (folder/'submission-receipt.json').exists(),'An admitted receipt exists: resume it, do not submit again'
    source=ROOT/'build/a03-judge-1/pipeline/problems/gaming-grid/solutions/reference.cpp'
    assert source.is_file()
    shutil.copyfile(ROOT/'build/phase-c-checkpoint1-1/accounts.json',folder/'accounts.json');(folder/'accounts.json').chmod(0o600)
    good=json.loads((WORK/'enrollment.json').read_text())
    wrong=json.loads(json.dumps(good))
    receipt=wrong['legacy']['pv000000000000000001']
    for f in receipt['manifest']['files']:
        if f['path']=='data.zip':f['sha256']='0'*64
    import sys
    sys.path.insert(0,str(ROOT/'deploy/phase-c'))
    # Standard-library digest matching the coordinator's canonical manifest.
    import hashlib
    receipt['manifest_digest']=hashlib.sha256(json.dumps(receipt['manifest'],sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()).hexdigest()
    assert receipt['manifest_digest']!=good['legacy']['pv000000000000000001']['manifest_digest']
    enrollment(wrong)
    args=['docker','run','--rm','--user',f'{os.getuid()}:{os.getgid()}','--network','host','--shm-size','256m',
      '--cap-drop','ALL','--security-opt','no-new-privileges','--mount',f'type=bind,src={folder},dst=/results',
      '--mount',f'type=bind,src={source},dst=/run/reference.cpp,readonly',
      '--mount',f'type=bind,src={HERE/"live_submission.py"},dst=/tests/browser.py,readonly',
      'cpjudge-b01-browser:local1','python','/tests/browser.py']
    path=WORK/(d.STAMP+'-one-real-browser.log')
    with path.open('wb') as log:
        os.chmod(path,0o600)
        proc=subprocess.Popen(args,stdout=log,stderr=subprocess.STDOUT)
        try:
            for _ in range(120):
                if (folder/'submission-receipt.json').exists():break
                if proc.poll() is not None:raise RuntimeError('Browser stopped before admission; inspect private log')
                time.sleep(.5)
            else:raise RuntimeError('No browser receipt within 60 seconds')
            sid=json.loads((folder/'submission-receipt.json').read_text())['submission_id']
            time.sleep(4)
            mismatch=assert_pending(sid,'mismatch-blocks-real-dispatch')
            # Actual native process may stop safely because nothing was sent.
            d.shell('guard-worker-reconnect-with-only-task-queued',"SID="+str(sid)+"\n"+"""from judge.models import Submission
assert not Submission.objects.filter(status__in=Submission.IN_PROGRESS_GRADING_STATUS).exclude(pk=SID).exists()
s=Submission.objects.get(pk=SID);assert s.status=='QU' and not s.test_cases.exists()
print('Only the task-owned queued submission exists; no worker execution interrupted.')
""")
            d.docker('reconnect-stop-only-idle-worker','stop','--signal','SIGINT','--time','20',WORKER)
            for _ in range(20):
                data=state(sid,'wait-worker-offline')
                if not data['worker_online']:break
                time.sleep(.5)
            else:raise RuntimeError('Worker did not go offline')
            offline=assert_pending(sid,'disconnect-keeps-pending',False)
            os.environ['CPJ_SITE_REPORT_DIR']=str(OUT)
            d.run('reconnect-worker-with-fresh-verifier',['python3','-B',str(ROOT/'deploy/site-local/b03.py'),'start'])
            time.sleep(4)
            reconnected=assert_pending(sid,'reconnect-still-needs-valid-readiness')
            enrollment(good)
            proc.wait(timeout=180)
            assert proc.returncode==0,'Inspect private browser log; resume existing receipt if needed'
        finally:
            enrollment(good)
            if proc.poll() is None:
                # Keep admitted work alive; do not terminate/re-submit it on an
                # operator failure. Browser process has its own bounded timeout.
                print('Browser still running; preserve receipt and inspect before resuming.',flush=True)
    records=json.loads((OUT/'commands.json').read_text())
    records.append({'name':'one-real-browser-submission','argv':args,'exit_status':proc.returncode,'private_log':str(path.relative_to(ROOT))})
    (OUT/'commands.json').write_text(json.dumps(records,indent=2)+'\n')
    finish()

def finish():
    folder=WORK/'browser'
    sid=json.loads((folder/'submission-receipt.json').read_text())['submission_id']
    def checkpoint(label):
        paths=sorted(WORK.glob('*-'+label+'.log'))
        row=json.loads(paths[-1].read_text().split('C11_STATE=',1)[1].splitlines()[0])
        assert row['status']=='QU' and row['result'] is None and row['case_count']==0
        return {k:v for k,v in row.items() if k!='error'}
    mismatch=checkpoint('mismatch-blocks-real-dispatch')
    offline=checkpoint('disconnect-keeps-pending')
    reconnected=checkpoint('reconnect-still-needs-valid-readiness')
    browser=json.loads((folder/'result.json').read_text())
    assert browser['displayed_verdict']=='AC' and browser['displayed_case_count']==103
    assert browser['actual_native_form_post_count']==1
    raw=d.shell('verify-one-real-native-result-and-case-rows',"SID="+str(sid)+"\n"+"""import json
from pathlib import Path
from judge.models import Submission
s=Submission.objects.get(pk=SID);cases=list(s.test_cases.order_by('case').values('case','status','points','total'))
assert s.status=='D' and s.result=='AC' and s.points==103 and s.case_points==103 and s.case_total==103
assert len(cases)==103 and all(c['status']=='AC' and c['points']==c['total']==1 for c in cases)
assert [c['case'] for c in cases]==list(range(1,104))
trace=[json.loads(l) for l in Path('/tmp/c11-native-trace.jsonl').read_text().splitlines()]
trace=[r for r in trace if r.get('submission-id')==SID]
sent=[r for r in trace if r['direction']=='sent' and r['name']=='submission-request']
assert len(sent)==1 and sent[0]['time-limit']==2 and sent[0]['memory-limit']==262144 and sent[0]['language']=='CPP23'
callbacks=[c for r in trace if r['direction']=='received-and-handled' and r['name']=='test-case-status' for c in r['cases']]
assert len(callbacks)==103 and all(c['status']==0 and c['points']==c['total-points']==1 for c in callbacks)
print('C11_RESULT='+json.dumps({'status':'PASS','submission_id':SID,'verdict':s.result,'case_count':len(cases),'native_packets':len(sent),
 'callback_cases':len(callbacks),'points':s.points,'case_points':s.case_points,'time_limit':2,'memory_kib':262144,
 'authenticated_worker_reconnected_before_dispatch':True,
 'compiler_warning_count':s.error.count('warning:') if s.error else 0}))
""")
    result=json.loads(raw.decode().split('C11_RESULT=',1)[1].splitlines()[0])
    result.update({'mismatch_pending':mismatch,'disconnected_pending':offline,'reconnected_mismatch_pending':reconnected,
                   'browser_native_form_posts':1,'browser_verdict':'AC','browser_case_count':103,
                   'all_browser_polls_authorized':all(x==200 for x in browser['authenticated_poll_responses']),
                   'real_problem_bytes_modified':False,'other_languages_or_new_versions_judged':False})
    env.save('live.json',result)
    print('PASS: same real browser submission pending across mismatch/reconnect, then dispatched once and AC103.',flush=True)
