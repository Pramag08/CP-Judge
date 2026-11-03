"""C09 native HTTP negatives and actual-byte sanitizer regression checks."""
import io,json,zipfile
from hashlib import sha256
from django.test import Client,override_settings
from django.urls import reverse
from PIL import Image
from cpjudge.c08_tests import CompatibilityTests
from cpjudge.imports import private_root
from cpjudge.models import ImportJob,Grant
from cpjudge.statement import build

class StatementTests(CompatibilityTests):
 def setUp(self):
  # Test settings use process-local cache; prevent earlier test logins from
  # consuming another test's production-style rate counter.
  from django.core.cache import cache
  cache.clear()
  super().setUp()
 # Inherit the seven C08 regressions, using their owned conversion-receipt fixture.
 def package(self,html='<p>$$$\\frac{a}{b}$$$</p><pre><div>1 2</div><div>3</div></pre><img src="i.png">',image=None):
  self.override=override_settings(CPJ_ARCHIVE_LIMITS={'upload_bytes':32*1024**2});self.override.enable();self.addCleanup(self.override.disable)
  j=self.stored();stream=io.BytesIO()
  if image is None:
   out=io.BytesIO();Image.new('RGB',(3,2),'red').save(out,format='PNG');image=out.getvalue()
  with zipfile.ZipFile(stream,'w') as z:
   z.writestr('problem.xml','<problem><statements><statement type="text/html" path="statements/english/problem.html"/></statements></problem>')
   z.writestr('statements/english/problem.html',html);z.writestr('statements/english/i.png',image)
   z.writestr('tests/hidden','PRIVATE-HIDDEN');z.writestr('checker.cpp','PRIVATE-CHECKER')
  data=stream.getvalue();(private_root()/j.archive_key).write_bytes(data)
  j.package_sha256=sha256(data).hexdigest();j.save();self.report['source_sha256']=j.package_sha256;self.write()
  return j
 def urls(self,j):
  _,assets,_=build(j)
  return f'/imports/{j.pk}/statement/',reverse('cpj_statement_asset',kwargs={'job_id':j.pk,'attempt':j.attempt,'asset':next(iter(assets))})
 def test_render_sample_lines_math_asset_headers_and_no_raw_data(self):
  j=self.package();page,asset=self.urls(j);c=self.logged('C5A');r=c.get(page)
  self.assertContains(r,'<pre>1 2\n3\n</pre>',html=False);self.assertContains(r,r'\(\frac{a}{b}\)')
  for response in (r,c.get(asset)):
   self.assertEqual(response.status_code,200);self.assertEqual(response['Cache-Control'],'private, no-store');self.assertEqual(response['X-Content-Type-Options'],'nosniff')
  a=c.get(asset);self.assertEqual(a['Content-Type'],'image/png');Image.open(io.BytesIO(a.content)).verify()
  self.assertNotContains(r,'PRIVATE-HIDDEN');self.assertNotContains(r,'PRIVATE-CHECKER')
 def test_logged_out_participant_unrelated_author_and_revocation_asset_denials(self):
  j=self.package();urls=self.urls(j)
  for c in (Client(),self.logged('C5P'),self.logged('C5B')):
   for url in urls:self.assertIn(c.get(url).status_code,(401,403,404))
  c=self.logged('C5A');Grant.objects.filter(user=j.owner).update(revoked=True)
  for url in urls:self.assertIn(c.get(url).status_code,(403,404))
 def test_stale_pending_failed_wrong_attempt_and_other_import_rejected(self):
  j=self.package();page,asset=self.urls(j);c=self.logged('C5A')
  for status in ('uploaded','queued','running','failed'):
   ImportJob.objects.filter(pk=j.pk).update(status=status)
   self.assertNotContains(c.get(page),'id="statement-preview"');self.assertEqual(c.get(asset).status_code,404)
  ImportJob.objects.filter(pk=j.pk).update(status='succeeded',attempt=2)
  self.assertEqual(c.get(asset).status_code,404);self.assertNotContains(c.get(page),'id="statement-preview"')
  self.assertEqual(c.get(asset.replace('/1/assets/','/2/assets/')).status_code,404)
  self.assertEqual(c.get(asset.replace(f'/imports/{j.pk}/','/imports/999999/')).status_code,404)
 def test_traversal_hidden_source_and_asset_key_are_not_file_routes(self):
  j=self.package();page,asset=self.urls(j);c=self.logged('C5A')
  for key in ('../problem.xml','%2e%2e%2fproblem.xml','checker.cpp','data.zip','tests/hidden','i.png','raw.zip','%252e%252e%252fproblem.xml'):
   r=c.get(asset.rsplit('/',1)[0]+'/'+key);self.assertIn(r.status_code,(400,403,404))
 def test_mime_spoofing_html_svg_and_corrupt_images_fail_closed(self):
  for bad in (b'<svg onload="alert(1)"/>',b'<html><script>alert(1)</script></html>',b'PNG fake'):
   # Reuse one stored attempt by changing original bytes/digest between subcases.
   if hasattr(self,'base'):
    import shutil;shutil.rmtree(self.base)
    ImportJob.objects.all().delete()
   j=self.package(image=bad);r=self.logged('C5A').get(f'/imports/{j.pk}/statement/')
   self.assertNotContains(r,'id="statement-preview"');self.assertContains(r,'Statement preview unavailable')
 def test_removals_reported_and_no_css_urls_events_or_active_dom(self):
  j=self.package(html='<p onclick="bad()" style="background:url(https://evil.invalid/x)">readable</p><script>bad()</script><style>@import "https://evil.invalid/s";</style><iframe src="https://evil.invalid/f"></iframe><svg onload="bad()"/><img src="i.png" onerror="bad()"><a href="javascript:bad()">text</a>')
  clean,assets,notices=build(j)
  self.assertTrue(notices);self.assertTrue(assets)
  for text in ('onclick','onerror','onload','evil.invalid','<script','<style','<iframe','<svg','href=','style='):self.assertNotIn(text,clean)
 def test_external_traversal_data_and_unsafe_math_show_no_partial_statement(self):
  from cpjudge.presentation import sanitize
  for src in ('https://evil.invalid/a','//evil.invalid/a','data:image/png,x','../tests/hidden','%2e%2e/a','a\\b','/a','i.png?x','i.png#x','%252e%252e/a'):
   with self.subTest(src=src),self.assertRaises((ValueError,KeyError)):
    sanitize('<p>partial</p><img src="'+src+'">',{},lambda k:k)
  for tex in (r'$$$\href{https://evil.invalid}{x}$$$',r'$$$\require{html}$$$',r'$$$\<b>href</b>{x}$$$'):
   with self.assertRaises(ValueError):sanitize(tex,{},lambda k:k)
 def test_source_digest_and_manifest_tampering_suppress_statement(self):
  j=self.package();page,asset=self.urls(j);c=self.logged('C5A')
  (private_root()/j.archive_key).write_bytes(b'changed')
  self.assertNotContains(c.get(page),'id="statement-preview"');self.assertEqual(c.get(asset).status_code,404)
 def test_image_polyglot_metadata_removed_and_resource_limits_fail_closed(self):
  import struct,zlib
  from cpjudge.presentation import raster,sanitize
  out=io.BytesIO();Image.new('RGB',(2,2),'blue').save(out,format='PNG')
  clean=raster(out.getvalue()+b'<script>private-polyglot</script>')
  self.assertNotIn(b'private-polyglot',clean);Image.open(io.BytesIO(clean)).verify()
  def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data))
  bomb=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',20000,20000,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(b''))+chunk(b'IEND',b'')
  with self.assertRaises(ValueError):raster(bomb)
  with self.assertRaises(ValueError):sanitize('<img src="a">'*33,{'a':out.getvalue()},lambda k:k)
  with self.assertRaises(ValueError):sanitize('<pre>lost text<div>line</div></pre>',{},lambda k:k)
 def test_declared_statement_traversal_and_xml_entities_rejected(self):
  j=self.package();path=private_root()/j.archive_key;original=path.read_bytes()
  for xml in ('<problem><statements><statement type="text/html" path="../checker.cpp"/></statements></problem>',
              '<!DOCTYPE x [<!ENTITY secret SYSTEM "file:///etc/passwd">]><problem>&secret;</problem>'):
   stream=io.BytesIO()
   with zipfile.ZipFile(io.BytesIO(original)) as src,zipfile.ZipFile(stream,'w') as dst:
    for name in src.namelist():dst.writestr(name,xml if name=='problem.xml' else src.read(name))
   path.write_bytes(stream.getvalue());j.package_sha256=sha256(stream.getvalue()).hexdigest();j.save()
   self.report['source_sha256']=j.package_sha256;self.write()
   r=self.logged('C5A').get(f'/imports/{j.pk}/statement/')
   self.assertNotContains(r,'id="statement-preview"');self.assertContains(r,'Statement preview unavailable')
