"""Create authentication and accurate Language metadata, never runtime records."""
import json
from pathlib import Path
from django.db import transaction
from judge.models import Judge, Language, RuntimeVersion, Submission

registration = json.loads(Path('/tmp/b03-registration.json').read_text())
with transaction.atomic():
    assert not Judge.objects.exists(), 'B03 initial enrollment requires explicit review of existing judges'
    assert not RuntimeVersion.objects.exists()
    assert not Submission.objects.filter(status__in=Submission.IN_PROGRESS_GRADING_STATUS).exists()
    language, created = Language.objects.get_or_create(key='CPP23', defaults={
        'name': 'C++23', 'short_name': 'C++23', 'common_name': 'C++', 'ace': 'c_cpp',
        'pygments': 'cpp', 'extension': 'cpp', 'info': '', 'description': '',
        'template': '#include <bits/stdc++.h>\n\nint main() { return 0; }\n'})
    assert language.name in ('C++23', 'GNU C++23') and language.extension == 'cpp' and not language.info
    Judge.objects.create(name=registration['id'], auth_key=registration['key'],
                         description='Local pinned B03 worker; no problems installed')
print(json.dumps({'registered': registration['id'], 'CPP23_language_created': created,
                  'runtime_records_created': 0, 'online_forced': False}))
