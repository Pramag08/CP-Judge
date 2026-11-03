"""Strict Polygon presentation adapter; runs in the locked website environment."""
import re
from html import escape
from urllib.parse import unquote, urlsplit
from lxml import html
import tinycss2

TAGS = {'div', 'span', 'p', 'ol', 'ul', 'li', 'pre', 'code', 'br', 'strong', 'b', 'em', 'i', 'sub', 'sup', 'table', 'thead', 'tbody', 'tr', 'td', 'th'}
CLASSES = {'problem-statement', 'header', 'title', 'time-limit', 'memory-limit', 'property-title',
           'input-file', 'input-standard', 'output-file', 'output-standard', 'legend',
           'input-specification', 'output-specification', 'section-title', 'sample-tests',
           'sample-test', 'input', 'output', 'content', 'note', 'tex-font-style-bf', 'tex-font-style-it'}
DROP = {'script', 'style', 'link', 'meta', 'iframe', 'object', 'embed', 'svg', 'math', 'form', 'input', 'button', 'textarea', 'img', 'video', 'audio', 'source', 'base'}
PROPERTIES = {'color', 'background-color', 'font-family', 'font-size', 'font-weight', 'font-style',
              'text-align', 'text-decoration', 'white-space', 'word-break', 'overflow-wrap',
              'display', 'border', 'border-width', 'border-style', 'border-color', 'border-collapse',
              'margin', 'margin-top', 'margin-bottom', 'margin-left', 'margin-right',
              'padding', 'padding-top', 'padding-bottom', 'padding-left', 'padding-right',
              'width', 'max-width', 'height', 'line-height', 'list-style-type'}
UNSAFE_TEX = re.compile(r'\\(?:href|url|html\w*|class|style|cssId|require|includegraphics|def|gdef|edef|let|newcommand|renewcommand|csname|unicode)\b', re.I)
TEX_COMMANDS = {'cdot', 'le', 'dots'}  # Exact selected statement subset; unknown commands fail closed.


def sanitize_statement(source):
    doc = html.document_fromstring(source)
    statements = doc.xpath('//div[contains(concat(" ",normalize-space(@class)," ")," problem-statement ")]')
    assert len(statements) == 1, 'Select exactly one Polygon statement'
    root = statements[0]
    for element in list(root.iterdescendants()):
        if not isinstance(element.tag, str):
            element.getparent().remove(element)
            continue
        tag = element.tag.lower()
        if tag in DROP:
            element.drop_tree()
        elif tag not in TAGS:
            element.drop_tag()
    for element in root.iter():
        classes = [c for c in element.get('class', '').split() if c in CLASSES]
        element.attrib.clear()
        if classes:
            element.set('class', ' '.join(classes))
    for pre in root.xpath('.//pre'):
        lines = pre.xpath('./div')
        text = '\n'.join(e.text_content() for e in lines) if lines else pre.text_content()
        for child in list(pre):
            pre.remove(child)
        pre.text = text.strip('\n') + '\n'
    # MathJax joins text nodes. Reject alternate delimiters and commands in the
    # complete imported text, including commands split across inline elements.
    complete = ''.join(root.itertext())
    assert set(re.findall(r'\\([A-Za-z]+)', complete)) <= TEX_COMMANDS, 'Unsupported imported TeX command'
    residual = re.sub(r'\$\$\$(.*?)\$\$\$', '', complete, flags=re.S)
    assert not any(token in residual for token in ('\\', '$$', '~')), 'Only Polygon math delimiters are supported'
    math = []
    def convert(text):
        if not text:
            return text
        def replace(match):
            tex = match.group(1)
            assert not UNSAFE_TEX.search(tex), 'Unsafe TeX command rejected'
            assert set(re.findall(r'\\([A-Za-z]+)', tex)) <= TEX_COMMANDS, 'Unsupported TeX command rejected'
            math.append(tex)
            return '\\(' + tex + '\\)'
        text = re.sub(r'\$\$\$(.*?)\$\$\$', replace, text, flags=re.S)
        assert '$$$' not in text, 'Unmatched Polygon math delimiters'
        return text
    for element in root.iter():
        element.text = convert(element.text)
        element.tail = convert(element.tail)
    fragment = '<div class="b06-imported">' + html.tostring(root, encoding='unicode', with_tail=False) + '</div>'
    assert not html.fromstring(fragment).xpath('.//script|.//iframe|.//img|.//*[@style]|.//*[@onclick]|.//*[@src]|.//*[@href]')
    return fragment, math


def sanitize_css(source):
    rules = []
    for rule in tinycss2.parse_stylesheet(source, skip_comments=True, skip_whitespace=True):
        if rule.type != 'qualified-rule':
            continue
        selector = tinycss2.serialize(rule.prelude).strip()
        if not re.fullmatch(r'[a-zA-Z0-9_. ,>:\-]+', selector):
            continue
        if any(x in selector.lower() for x in ('html', 'body', ':root', ':visited')):
            continue
        selectors = ['.b06-imported ' + s.strip() for s in selector.split(',') if s.strip()]
        declarations = []
        for item in tinycss2.parse_declaration_list(rule.content, skip_comments=True, skip_whitespace=True):
            if item.type != 'declaration' or item.lower_name not in PROPERTIES:
                continue
            value = tinycss2.serialize(item.value)
            if any(t.type in ('url', 'function', 'error', 'at-keyword') for t in item.value):
                continue
            if any(s in value.lower() for s in ('url', 'expression', 'javascript', '\\', '@')):
                continue
            declarations.append(item.lower_name + ':' + value.strip())
        if declarations and selectors:
            rules.append(','.join(selectors) + '{' + ';'.join(declarations) + '}')
    return '\n'.join(rules) + '\n'
