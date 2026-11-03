"""Install the bounded asset overlay, retaining original files outside finders.
source mode runs as site; library mode runs as the package-directory owner.
"""
import argparse
import hashlib
from pathlib import Path

parser=argparse.ArgumentParser()
parser.add_argument('mode',choices=['source','library'])
args=parser.parse_args()
if args.mode=='source':
    old=Path('/app/resources/wpadmin/css/wpadmin.site.css')
    target=Path('/app/resources/cpjudge/wpadmin-site.css')
    target.parent.mkdir(parents=True,exist_ok=True)
    if old.exists():
        assert hashlib.sha256(old.read_bytes()).hexdigest()=='18db61092454134208d053cae8bcd72fc55c1b457d2603c7d7258c0c3f90660b'
        if target.exists():assert target.read_bytes()==old.read_bytes()
        else:target.write_bytes(old.read_bytes())
        old.unlink()
    assert target.exists()
    settings=Path('/app/dmoj/local_settings.py')
    text=settings.read_text()
    marker='# B01 follow-up: collected output is not a static source directory.'
    if marker not in text:
        settings.write_text(text+'\n'+marker+'\n'+
            "STATICFILES_FINDERS = tuple(f for f in STATICFILES_FINDERS if f != 'compressor.finders.CompressorFinder')\n"+
            "STATIC_ROOT = '/app/static-followup'\n")
else:
    import importlib.metadata
    package=Path(importlib.metadata.distribution('dmoj-wpadmin').locate_file('wpadmin'))
    old=package/'static/admin/js/jquery.init.js'
    retained=package/'cpjudge-retained/jquery.init.js'
    if old.exists():
        assert hashlib.sha256(old.read_bytes()).hexdigest()=='d73d4ac2d73b9594c5696f2ff3e8159d58d01cc5eee7e218a6562e9e7ab889c2'
        retained.parent.mkdir(exist_ok=True)
        old.rename(retained)
    assert retained.exists()
    # Keep WPadmin's visual template; use the canonical actions.js auto-initializer.
    template=package/'templates/admin/change_list.html'
    text=template.read_text()
    obsolete='{% if action_form %}{% if actions_on_top or actions_on_bottom %}\n<script type="text/javascript">\n(function($) {\n    $(document).ready(function($) {\n        $("tr input.action-select").actions({\'allToggle\': \'th.action-checkbox-column input\'});\n    });\n})(django.jQuery);\n</script>\n{% endif %}{% endif %}'
    marker='{# Django 5.2 actions.js in media.js initializes the real Actions API itself. #}'
    if obsolete in text:
        backup=package/'cpjudge-retained/change_list.html'
        if not backup.exists():backup.write_text(text)
        template.write_text(text.replace(obsolete,marker))
    else:assert marker in text
print('Applied bounded '+args.mode+' overlay; original CSS retained by namespace and WPadmin shim retained outside static finders.')
