"""Add only a fixed permission-checked CSS URL and native template link."""
import hashlib
import json
import re
from pathlib import Path
from django.conf import settings
from django.contrib.staticfiles import finders

urls = Path('/app/dmoj/urls.py')
text = urls.read_text()
line = "\n# B06: private sanitized presentation asset; native problem view stays unchanged.\nfrom judge.views.imported_statement import imported_statement_asset\nurlpatterns.append(path('problem/<str:problem>/statement-assets/<str:asset>', imported_statement_asset, name='imported_statement_asset'))\n"
if "name='imported_statement_asset'" not in text:
    urls.write_text(text + line)
template = Path('/app/templates/problem/problem.html')
text = template.read_text()
link = "\n    {% if problem.code == 'pv000000000000000001' %}<link rel=\"stylesheet\" href=\"{{ url('imported_statement_asset', problem=problem.code, asset='statement.css') }}\">{% endif %}\n"
if 'imported_statement_asset' not in text:
    assert '{% block content_media %}' in text
    template.write_text(text.replace('{% block content_media %}', '{% block content_media %}' + link, 1))
text = template.read_text()
native = "{{ description|markdown(problem.markdown_style, MATH_ENGINE)|reference|str|safe }}"
replacement = "{% if problem.code == 'pv000000000000000001' %}{{ description|imported_statement(problem.code) }}{% else %}" + native + "{% endif %}"
if 'description|imported_statement' not in text:
    assert text.count(native) == 1
    template.write_text(text.replace(native, replacement))
init = Path('/app/judge/jinja2/__init__.py')
text = init.read_text()
if '\nfrom . import imported_statement\n' not in text:
    init.write_text(text + '\n# B06 receipt-bound sanitized fragment, no general full-markup bypass.\nfrom . import imported_statement\n')
fonts = []
for value in [*finders.find('plugins/css/semantic.css', all=True), str(Path(settings.STATIC_ROOT) / 'plugins/css/semantic.css')]:
    path = Path(value)
    if not path.is_file():
        continue
    css = path.read_text()
    original = hashlib.sha256(css.encode()).hexdigest()
    css, removed = re.subn(r'@import\s+url\([\"\']?https://fonts\.googleapis\.com/[^)]*\)\s*;', '', css)
    assert removed in (0, 1)
    assert 'fonts.googleapis.com' not in css
    if removed:
        path.write_text(css)
    fonts.append({'path': str(path), 'before_sha256': original, 'after_sha256': hashlib.sha256(css.encode()).hexdigest(), 'imports_removed': removed})
print('JOURNEY_RESULT=' + json.dumps({'template_layout_retained': True,
      'native_semantic_font_fallback': fonts,
      'route_sha256': hashlib.sha256(urls.read_bytes()).hexdigest(),
      'template_sha256': hashlib.sha256(template.read_bytes()).hexdigest()}))
