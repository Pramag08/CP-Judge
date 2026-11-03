"""Exercise actual resource enforcement in the trusted child, without a package."""
import json,os,subprocess,sys,tempfile,time
from pathlib import Path
from django.test import SimpleTestCase

class ChildLimitsTests(SimpleTestCase):
 def test_actual_child_limits_and_independent_wall_timeout(self):
  with tempfile.TemporaryDirectory(prefix='cpj-resource-proof-') as tmp:
   code='''import django,json,resource,time,sys
from pathlib import Path
from cpjudge.convert_runner import main
root=Path(sys.argv[1])
def trusted_setup():
 (root/'limits.json').write_text(json.dumps({name:resource.getrlimit(getattr(resource,name)) for name in ('RLIMIT_AS','RLIMIT_CPU','RLIMIT_FSIZE','RLIMIT_NOFILE')}))
 time.sleep(10)
django.setup=trusted_setup
sys.argv=['runner','0',str(root),'0','1']
sys.exit(main())
'''
   start=time.monotonic()
   result=subprocess.run([sys.executable,'-c',code,tmp],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=5)
   self.assertEqual(result.returncode,1)
   self.assertLess(time.monotonic()-start,5)
   self.assertFalse(json.loads((Path(tmp)/'result.json').read_text())['ok'])
   limits=json.loads((Path(tmp)/'limits.json').read_text())
   self.assertEqual(limits['RLIMIT_AS'],[768*1024**2]*2)
   self.assertEqual(limits['RLIMIT_CPU'],[60,60])
   self.assertEqual(limits['RLIMIT_FSIZE'],[256*1024**2]*2)
   self.assertEqual(limits['RLIMIT_NOFILE'],[128,128])
