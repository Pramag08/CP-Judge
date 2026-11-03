"""Prepare private sanitized presentation, with adversarial checks, no DB writes."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from lxml import html

spec = importlib.util.spec_from_file_location('b06_sanitize', '/tmp/b06_statement_sanitize.py')
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
fragment, math = module.sanitize_statement(PAYLOAD['html'])
css = module.sanitize_css(PAYLOAD['css'])
assert css and '.b06-imported' in css
attack = '<div class="problem-statement" onclick="alert(1)"><script>alert(1)</script><img src="https://evil.invalid/x" onerror="alert(1)"><iframe srcdoc="x"></iframe><a href="javascript:alert(1)">safe words</a><p style="background:url(https://evil.invalid)">text</p></div>'
clean, _ = module.sanitize_statement(attack)
assert all(bad not in clean.lower() for bad in ('alert', 'onclick', 'onerror', 'src=', 'href=', 'style=', 'iframe', 'script', 'evil.invalid'))
assert 'safe words' in clean
badcss = '@import "https://evil.invalid"; .x{background-image:url(https://evil.invalid);position:fixed;color:red} body{color:black}'
clean_css = module.sanitize_css(badcss)
assert 'color:red' in clean_css and all(word not in clean_css for word in ('url', 'position', '@import', 'evil.invalid', 'body'))
try:
    module.sanitize_statement('<div class="problem-statement">$$$\\href{javascript:x}{bad}$$$</div>')
except AssertionError:
    pass
else:
    raise AssertionError('Unsafe TeX accepted')
for value in (r'\(\href{javascript:x}{bad}\)', r'\[\href{javascript:x}{bad}\]',
              r'$$\href{javascript:x}{bad}$$', r'~\href{javascript:x}{bad}~',
              r'\(<span>\</span><span>href</span>{javascript:x}{bad}\)'):
    try:
        module.sanitize_statement('<div class="problem-statement">' + value + '</div>')
    except AssertionError:
        pass
    else:
        raise AssertionError('Raw/split native math escaped validation')
root = Path('/app/private-imports/pv000000000000000001'); root.mkdir(parents=True, mode=0o700, exist_ok=True); root.chmod(0o700)
files = {'description.html': fragment.encode(), 'statement.css': css.encode()}
for name, data in files.items():
    path = root / name
    if path.exists():
        assert path.read_bytes() == data, 'Refuse different presentation under this receipt'
    else:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600); os.write(fd, data); os.close(fd)
receipt = {'code': 'pv000000000000000001', 'package_sha256': '260abce9770f2c88cf8c93271cbfcbd6cea3f028c6eda536ad16256731d8a769',
           'judge_manifest_digest': '7e7b7ec333912da774b066e821eae4c2cb9cb9426ea3417320352d128b5dcf90',
           'description_sha256': hashlib.sha256(files['description.html']).hexdigest(),
           'css_sha256': hashlib.sha256(files['statement.css']).hexdigest(),
           'source_html_sha256': hashlib.sha256(PAYLOAD['html'].encode()).hexdigest(),
           'source_css_sha256': hashlib.sha256(PAYLOAD['css'].encode()).hexdigest(), 'math_expressions': len(math)}
path = root / 'receipt.json'
if path.exists():
    assert json.loads(path.read_text()) == receipt
else:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600); os.write(fd, json.dumps(receipt, indent=2).encode()); os.close(fd)
print('JOURNEY_RESULT=' + json.dumps({'status': 'PASS', **receipt, 'adversarial_html_css_tex_checks': 'PASS',
      'imported_executable_tags_urls_removed': True, 'selected_statement_images': 0, 'judging': 'NOT TESTED'}, indent=2))
