"""C09: attempt-bound sanitized statement only; no general archive file server."""
from hashlib import sha256
from pathlib import PurePosixPath
import re
import zipfile
from defusedxml import ElementTree
from defusedxml.common import DefusedXmlException
from django.urls import reverse
from .compatibility import preview
from .imports import private_root, archive_limits
from .presentation import sanitize

UNAVAILABLE='Statement preview unavailable: unsupported HTML, math or image content, missing assets, or invalid conversion receipt. No partial statement is shown. Use UTF-8 HTML, Polygon $$$ math and local PNG/JPEG/WebP images under statements/. PDF and executable SVG/HTML assets are unsupported.'


def local_path(value):
    # XML paths are literal archive member names, never URLs or filesystem paths.
    if (not isinstance(value,str) or not value or '\\' in value or ':' in value
            or '%' in value or value.startswith('/') or
            any(p in ('','.','..') for p in value.split('/'))):
        raise ValueError('Invalid statement path')
    return PurePosixPath(value)


def build(job):
    """Read only declared HTML + referenced raster bytes from a verified upload.

    Nothing is extracted/written or publicly cached. C08 verifies the current
    successful attempt/owner manifest and output. A digest binds source bytes to
    that conversion; strict archive preflight was enforced before conversion.
    """
    if not preview(job):raise ValueError('No current successful conversion')
    if not re.fullmatch(r'[a-f0-9]{48}\.zip',job.archive_key):raise ValueError('Invalid archive reference')
    path=private_root()/job.archive_key
    if path.is_symlink() or path.stat().st_size>archive_limits().upload_bytes:
        raise ValueError('Invalid upload')
    with path.open('rb') as source:
        digest=sha256()
        for block in iter(lambda:source.read(65536),b''):digest.update(block)
        if digest.hexdigest()!=job.package_sha256:raise ValueError('Source changed')
        source.seek(0)
        with zipfile.ZipFile(source) as archive:
            def read(name,limit):
                info=archive.getinfo(name)
                if info.file_size>limit:raise ValueError('Statement budget exceeded')
                with archive.open(info) as member:data=member.read(limit+1)
                if len(data)>limit:raise ValueError('Statement budget exceeded')
                return data
            doc=ElementTree.fromstring(read('problem.xml',1024**2))
            statements=doc.findall('statements/statement')
            selected=next((s for s in statements if s.get('type')=='text/html'),None)
            if selected is None:raise ValueError('HTML required')
            name=local_path(selected.get('path'))
            if name.parts[0]!='statements':raise ValueError('Statement outside approved area')
            html=read(str(name),4*1024**2).decode('utf-8-sig')
            class Assets:
                total=0
                def __contains__(self,key):
                    target=name.parent/local_path(key)
                    return target.parts[0]=='statements' and str(target) in archive.namelist()
                def __getitem__(self,key):
                    target=name.parent/local_path(key)
                    if target.parts[0]!='statements':raise ValueError('Unapproved asset area')
                    data=read(str(target),8*1024**2)
                    self.total+=len(data)
                    if self.total>24*1024**2:raise ValueError('Image total budget exceeded')
                    return data
            notices=[]
            if len(statements)>1:notices.append('Only the first declared HTML language is previewed; other statement languages/formats are not shown.')
            fragment,assets=sanitize(html,Assets(),lambda key:reverse('cpj_statement_asset',kwargs={
                'job_id':job.pk,'attempt':job.attempt,'asset':key}),notices)
            return fragment,assets,notices


def headers(response):
    response['Cache-Control']='private, no-store'
    response['X-Content-Type-Options']='nosniff'
    response['Referrer-Policy']='no-referrer'
    return response


def statement_preview(request,job_id):
    from django.shortcuts import render
    from .imports import owned
    job=owned(request.user,job_id)
    fragment=None;notices=[]
    try:fragment,_,notices=build(job)
    except (ValueError,OSError,KeyError,zipfile.BadZipFile,ElementTree.ParseError,DefusedXmlException):notices=[UNAVAILABLE]
    # Reauthorize after file work; permission/attempt state remains authoritative.
    current=owned(request.user,job_id)
    if (current.status,current.attempt,current.token)!=('succeeded',job.attempt,job.token):
        fragment=None;notices=[UNAVAILABLE]
    response=render(request,'cpjudge/statement.html',{'title':'Private statement preview','job':current,
        'fragment':fragment,'notices':notices,'REQUIRE_JAX':True})
    return headers(response)


def statement_asset(request,job_id,attempt,asset):
    from django.http import Http404,HttpResponse
    from .imports import owned
    job=owned(request.user,job_id)
    if job.attempt!=attempt or not re.fullmatch(r'[a-f0-9]{64}\.png',asset):raise Http404
    try:_,assets,_=build(job)
    except (ValueError,OSError,KeyError,zipfile.BadZipFile,ElementTree.ParseError,DefusedXmlException):raise Http404
    current=owned(request.user,job_id)
    if (current.status,current.attempt,current.token)!=('succeeded',attempt,job.token) or asset not in assets:raise Http404
    response=headers(HttpResponse(assets[asset],content_type='image/png'))
    response['Content-Security-Policy']="default-src 'none'; sandbox"
    return response
