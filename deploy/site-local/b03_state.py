"""Read native bridge-owned state. Never set online flags/runtime records."""
import json
from judge.models import Judge

j = Judge.objects.get(name='cpjudge-local-worker')
print(json.dumps({'name': j.name, 'online': j.online,
                  'executors': list(j.runtimes.order_by('key').values_list('key', flat=True)),
                  'runtime_versions': list(j.runtimeversion_set.order_by('language__key', 'priority').values('language__key', 'name', 'version')),
                  'problems': j.problems.count(), 'start_time': str(j.start_time)}, indent=2))
