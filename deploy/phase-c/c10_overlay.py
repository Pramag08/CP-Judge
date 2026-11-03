"""Extend B06's exact-receipt native renderer for private C10 version codes."""
from pathlib import Path
p=Path('/app/templates/problem/problem.html');text=p.read_text()
old="{% if problem.code == 'pv000000000000000001' %}{{ description|imported_statement(problem.code) }}"
new="{% if problem.code == 'pv000000000000000001' or problem.code.startswith('pv9') %}{{ description|imported_statement(problem.code) }}"
if new not in text:
    assert text.count(old)==1
    text=text.replace(old,new)
link='''
    {% if problem.code.startswith('pv9') %}<link rel="stylesheet" href="{{ url('cpj_version_asset', problem=problem.code, asset='statement.css') }}">{% endif %}
'''
if "url('cpj_version_asset'" not in text:text=text.replace('{% block content_media %}','{% block content_media %}'+link,1)
p.write_text(text)
print('Extended B06 receipt renderer; existing problem branch preserved.')
