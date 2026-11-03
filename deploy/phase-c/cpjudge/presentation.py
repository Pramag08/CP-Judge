"""Inert HTML and raster adapter for private compatibility previews.

Never serve original HTML/SVG or unvalidated assets. Math is local MathJax input
from a bounded allowlist, not arbitrary TeX/HTML commands.
"""
from hashlib import sha256
from io import BytesIO
import re
from urllib.parse import unquote, urlsplit
from lxml import html
from PIL import Image

TAGS={'div','span','p','ol','ul','li','pre','code','br','strong','b','em','i','sub','sup',
      'h1','h2','h3','h4','table','thead','tbody','tr','td','th','img'}
DROP={'script','style','link','meta','iframe','object','embed','svg','math','form','input','button',
      'textarea','video','audio','source','base','template','noscript'}
TEX=frozenset(('frac dfrac tfrac sqrt sum prod int lim sin cos tan log ln min max cdot times div '
    'le leq ge geq neq ne lt gt in notin subset subseteq cup cap emptyset forall exists '
    'alpha beta gamma delta epsilon theta lambda mu pi rho sigma phi omega Delta Sigma '
    'ldots cdots dots left right lbrace rbrace lceil rceil lfloor rfloor '
    'text mathrm mathbf mathit mathbb overline underline vec binom pm mp infty '
    'begin end aligned cases matrix pmatrix bmatrix quad qquad displaystyle').split())


def raster(data):
    if len(data)>8*1024**2:
        raise ValueError('Statement image exceeds 8 MiB')
    # Reject SVG, HTML and polyglot active payloads by decoding and re-encoding.
    try:
        with Image.open(BytesIO(data)) as image:
            if image.format not in {'PNG','JPEG','WEBP'}:
                raise ValueError('Only PNG/JPEG/WebP statement images are supported')
            if image.width*image.height>16_000_000 or image.n_frames!=1:
                raise ValueError('Image pixel/frame limit exceeded')
            image.load()
            clean=BytesIO()
            image.convert('RGBA').save(clean,format='PNG')
    except (OSError,Image.DecompressionBombError) as exc:
        raise ValueError('Invalid or oversized raster image') from exc
    return clean.getvalue()


CLASSES={'problem-statement','header','title','time-limit','memory-limit','property-title',
         'input-file','input-standard','output-file','output-standard','legend',
         'input-specification','output-specification','section-title','sample-tests',
         'sample-test','input','output','content','note','tex-font-style-bf','tex-font-style-it'}


def sanitize(source, assets, url_for, notices=None):
    if len(source.encode())>4*1024**2:
        raise ValueError('HTML statement exceeds 4 MiB')
    root=html.fragment_fromstring(source,create_parent='div')
    notices = notices if notices is not None else []
    removed=False
    sanitized_assets={}
    if len(root.xpath('.//img'))>32:raise ValueError('Too many statement images')
    for node in list(root.iterdescendants()):
        if not isinstance(node.tag,str):
            node.getparent().remove(node);removed=True
        elif node.tag.lower() in DROP:
            node.drop_tree();removed=True
        elif node.tag.lower() not in TAGS:
            node.drop_tag();removed=True
    for node in root.iter():
        src=node.get('src') if node.tag=='img' else None
        classes=[c for c in node.get('class','').split() if c in CLASSES]
        if any(k not in {'class','src','alt'} for k in node.attrib):removed=True
        if node.get('class','').split()!=classes:removed=True
        node.attrib.clear()
        if classes:node.set('class',' '.join(classes))
        if node.tag=='img':
            if not src:
                raise ValueError('Image has no local source')
            parsed=urlsplit(src)
            path=unquote(parsed.path)
            if (parsed.scheme or parsed.netloc or parsed.query or parsed.fragment or '\\' in path
                    or ':' in path or path.startswith('/') or any(x in ('','..','.') for x in path.split('/'))):
                raise ValueError('Use a local PNG/JPEG/WebP image path without traversal or external URLs')
            if path not in assets:
                raise ValueError('Missing local statement image: '+path)
            data=raster(assets[path])
            key=sha256(data).hexdigest()+'.png'
            if sum(map(len,sanitized_assets.values()))+len(data)>24*1024**2:
                raise ValueError('Rendered image total budget exceeded')
            sanitized_assets[key]=data
            node.set('src',url_for(key))
            node.set('alt','Statement image')
    # Reuse B06's Polygon sample-line normalization, preserving line breaks.
    for pre in root.xpath('.//pre'):
        lines=pre.xpath('./div')
        if lines:
            if (pre.text and pre.text.strip()) or any(c.tag!='div' or (c.tail and c.tail.strip()) for c in pre):
                raise ValueError('Unsupported mixed sample line markup')
            text='\n'.join(e.text_content() for e in lines)
            for child in list(pre):pre.remove(child)
            pre.text=text.strip('\n')+'\n'
    if removed:
        notices.append('Removed unsupported markup, attributes, links, scripts or uploaded CSS. Review the statement for lost meaning; preview does not approve publication.')
    complete=''.join(root.itertext())
    if set(re.findall(r'\\([A-Za-z]+)',complete))-TEX:
        raise ValueError('Unsupported or unsafe math command; use the supported local math subset')
    residual=re.sub(r'\$\$\$(.*?)\$\$\$','',complete,flags=re.S)
    if any(value in residual for value in ('\\','$$','~')):
        raise ValueError('Use Polygon $$$ math delimiters; alternative math syntax is unsupported')
    def math(text):
        if text is None:
            return None
        text=re.sub(r'\$\$\$(.*?)\$\$\$',lambda m:r'\('+m[1]+r'\)',text,flags=re.S)
        if '$$$' in text:
            raise ValueError('Unmatched or split math delimiter')
        return text
    for node in root.iter():
        node.text=math(node.text)
        node.tail=math(node.tail)
    return html.tostring(root,encoding='unicode',with_tail=False),sanitized_assets
