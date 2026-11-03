"""Native private metadata install/verify. No Submission or RuntimeVersion writes."""
import json
import hashlib
from pathlib import Path
from django.db import transaction
from judge.models import Problem, ProblemGroup, Language, LanguageLimit, Judge, Submission, ProblemData

code = REQUEST['native_code']
fields = dict(REQUEST['site_values'])
languages = fields.pop('allowed_languages')
fields['name'] = REQUEST['title']
created = False
with transaction.atomic():
    assert not Submission.objects.filter(status__in=Submission.IN_PROGRESS_GRADING_STATUS).exists()
    worker = Judge.objects.get(name='cpjudge-local-worker', online=True)
    assert set(languages) == {'CPP23'} and worker.runtimes.filter(key='CPP23').exists()
    problem = Problem.objects.select_for_update().filter(code=code).first()
    if MODE == 'preflight' and problem is None:
        result = {'exists': False}
    else:
        if problem is None:
            assert MODE == 'install', 'Problem is not installed'
            category, _ = ProblemGroup.objects.get_or_create(name=REQUEST['category']['name'], defaults={'full_name': REQUEST['category']['full_name']})
            assert category.full_name == REQUEST['category']['full_name'], 'Existing category conflicts'
            problem = Problem(code=code, group=category, **fields)
            problem.full_clean(exclude=['description'])
            problem.save()
            problem.allowed_languages.set(Language.objects.filter(key__in=languages))
            created = True
        if problem.description != fields['description']:
            # B06 may add only a separately receipt-bound sanitized presentation.
            receipt = json.loads((Path('/app/private-imports') / code / 'receipt.json').read_text())
            assert receipt['code'] == code and receipt['package_sha256'] == REQUEST['package_sha256']
            assert receipt['judge_manifest_digest'] == REQUEST['judge_manifest_digest']
            assert hashlib.sha256(problem.description.encode()).hexdigest() == receipt['description_sha256']
            fields['description'] = problem.description
        assert all(getattr(problem, k) == v for k, v in fields.items()), 'Frozen problem metadata differs'
        assert problem.group.name == REQUEST['category']['name'] and problem.group.full_name == REQUEST['category']['full_name']
        assert list(problem.allowed_languages.order_by('key').values_list('key', flat=True)) == languages
        assert not LanguageLimit.objects.filter(problem=problem).exists(), 'LanguageLimit overrides forbidden'
        assert not ProblemData.objects.filter(problem=problem).exists(), 'Do not regenerate manually managed data'
        assert not problem.is_public and problem.is_manually_managed
        result = {'exists': True, 'created': created, 'problem_pk': problem.pk, 'native_code': problem.code,
                  'site_values': {k: (hashlib.sha256(problem.description.encode()).hexdigest() if k == 'description' else getattr(problem, k)) for k in fields}, 'allowed_languages': languages,
                  'language_limit_rows': 0, 'worker_online': worker.online,
                  'native_worker_recognizes_problem': worker.problems.filter(pk=problem.pk).exists(),
                  'submission_count': Submission.objects.count(), 'judging': 'NOT TESTED'}
print('OPERATOR_RESULT=' + json.dumps(result, indent=2))
