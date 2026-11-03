"""Render only the exact private, sanitized, receipt-bound statement fragment."""
import hashlib
import json
from pathlib import Path
from markupsafe import Markup
from . import registry


@registry.filter
def imported_statement(value, code):
    if code.startswith('pv9'):
        from cpjudge.publication import published_description
        return published_description(value,code)
    if code != 'pv000000000000000001':
        raise ValueError('No imported presentation receipt')
    receipt = json.loads((Path('/app/private-imports') / code / 'receipt.json').read_text())
    if hashlib.sha256(value.encode()).hexdigest() != receipt['description_sha256']:
        raise ValueError('Imported presentation differs from sanitized receipt')
    return Markup(value)
