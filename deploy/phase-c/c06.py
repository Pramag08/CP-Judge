"""C06 extraction-only service checks; secret-bearing output stays private."""
import json,sys
from pathlib import Path
import c05 as driver
ROOT=driver.ROOT
WORK=ROOT/'build/phase-c-c06-1';OUT=ROOT/'reports/phase-c-c06-1'
WORK.mkdir(parents=True,exist_ok=True,mode=0o700);WORK.chmod(0o700)
OUT.mkdir(parents=True,exist_ok=True)
driver.WORK=WORK;driver.OUT=OUT
if sys.argv[1]=='stage':
 driver.docker('stage-extraction-service','cp',str(driver.HERE/'cpjudge')+'/.',driver.SITE+':/app/cpjudge')
 driver.docker('stage-existing-strict-adapter','cp',str(ROOT/'compat')+'/.',driver.SITE+':/app/compat')
 driver.docker('stage-source-pins','cp',str(ROOT/'dependencies.json'),driver.SITE+':/app/dependencies.json')
 pin=driver.docker('verify-existing-pcc-pin','exec','--user','1000:1000',driver.SITE,'git','-C','/tmp/cpj-pcc','rev-parse','HEAD')
 assert pin.decode().strip()==json.loads((ROOT/'dependencies.json').read_text())['converter']['commit']
elif sys.argv[1]=='tests':
 driver.docker('extraction-service-tests','exec','--user','1000:1000','-e','PCC_ROOT=/tmp/cpj-pcc',driver.SITE,'python','manage.py','test','cpjudge.integration_tests.NativeExtractionTests','cpjudge.integration_tests.NativeUploadHTTPTests','cpjudge.tests.UploadCoreTests','--settings=dmoj.cpj_integration_settings','--keepdb','--noinput','-v','2')
elif sys.argv[1]=='live':
 sid=json.loads((ROOT/'reports/phase-c-c05-1/browser.json').read_text())['accepted_job_id']
 code='JOB_ID='+str(sid)+'\n'+'''import json,hashlib,os
from pathlib import Path
from unittest.mock import patch
from django.core.exceptions import ValidationError
from cpjudge.imports import extracted_upload,private_root
from cpjudge.models import ImportJob
from compat.archive import extract_zip
job=ImportJob.objects.select_related('owner').get(pk=JOB_ID)
before=list(ImportJob.objects.filter(pk=job.pk).values())[0]
root=private_root();original=root/job.archive_key
hash_before=hashlib.sha256(original.read_bytes()).hexdigest()
existing=set(root.iterdir())
with patch.dict(os.environ,{'PCC_ROOT':'/tmp/cpj-pcc','GIT_CONFIG_COUNT':'1','GIT_CONFIG_KEY_0':'safe.directory','GIT_CONFIG_VALUE_0':'/tmp/cpj-pcc'}),patch('compat.archive.extract_zip',wraps=extract_zip) as extractor,patch('compat.convert.convert',side_effect=AssertionError('Conversion forbidden')):
 try:
  with extracted_upload(job.owner,job.pk):raise AssertionError('C05 non-Polygon fixture unexpectedly accepted')
 except ValidationError as exc:
  assert str(root) not in str(exc)
  assert 'problem.xml' in str(exc)
 assert extractor.call_count==1
assert hashlib.sha256(original.read_bytes()).hexdigest()==hash_before
assert set(root.iterdir())==existing
assert list(ImportJob.objects.filter(pk=job.pk).values())[0]==before
print('C06_RESULT='+json.dumps({'status':'PASS','actual_C05_HTTP_upload_reached_strict_extractor':True,'non_Polygon_fixture_rejected_safely':True,'original_and_other_jobs_preserved':True,'record_unchanged':True,'conversion_started':False,'new_website_extraction_action':False}))
'''
 raw=driver.shell('actual-stored-http-upload-extraction',code)
 result=json.loads(raw.decode().split('C06_RESULT=',1)[1].splitlines()[0])
 (OUT/'live-service.json').write_text(json.dumps(result,indent=2)+'\n')
else:raise SystemExit('Unknown action')
