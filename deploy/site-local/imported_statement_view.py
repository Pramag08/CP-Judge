"""Permission-checked, fixed-name sanitized presentation asset; no judge data."""
from pathlib import Path
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from judge.models import Problem


def imported_statement_asset(request, problem, asset):
    obj = get_object_or_404(Problem, code=problem)
    if problem != 'pv000000000000000001' or asset != 'statement.css' or not obj.is_accessible_by(request.user):
        raise Http404()
    path = Path('/app/private-imports') / problem / 'statement.css'
    if not path.is_file():
        raise Http404()
    response = HttpResponse(path.read_bytes(), content_type='text/css; charset=utf-8')
    response['X-Content-Type-Options'] = 'nosniff'
    response['Cache-Control'] = 'private, no-store'
    response['Content-Security-Policy'] = "default-src 'none'; sandbox"
    return response
