"""Executed in the selected Django/MariaDB runtime; output has no credentials."""
import hashlib
import json
import platform
from importlib.metadata import version
from pathlib import Path
from unittest.mock import patch
from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.state import ProjectState
from django.db.migrations.autodetector import MigrationAutodetector
from judge.models import Profile, Judge, RuntimeVersion
from judge.models.choices import make_timezones, TIMEZONE

loader = MigrationLoader(connection)
loader.check_consistent_history(connection)
assert not MigrationAutodetector(loader.project_state(), ProjectState.from_apps(__import__('django').apps.apps)).changes(graph=loader.graph)
assert ('judge', '0153_reconcile_model_metadata') in loader.applied_migrations
assert list(Profile._meta.get_field('timezone').choices) == TIMEZONE == make_timezones()
with patch('judge.models.choices.available_timezones', return_value={'Asia/Kolkata', 'UTC'}):
    assert not MigrationAutodetector(loader.project_state(), ProjectState.from_apps(__import__('django').apps.apps)).changes(graph=loader.graph)
cache.set('b01-baseline', 'ok', 30)
assert cache.get('b01-baseline') == 'ok'
with connection.cursor() as c:
    c.execute('SELECT VERSION()'); dbversion = c.fetchone()[0]
    constraints = connection.introspection.get_constraints(c, 'judge_class')
assert any(v['unique'] and v['columns'] == ['name'] for v in constraints.values())
print(json.dumps({
    'python': platform.python_version(),
    'distributions': {key: version(key) for key in ['Django','mysqlclient','celery','tzdata']},
    'database': dbversion, 'applied_migrations': len(loader.applied_migrations),
    'new_migration_applied': True, 'migration_history_consistent': True,
    'autodetector_changes': {}, 'timezone_callable_list_equivalent': True,
    'changed_zoneinfo_inventory_does_not_create_migration': True,
    'timezone_choices_count': sum(len(items) for _, items in make_timezones()),
    'cache_round_trip': 'PASS', 'class_unconditional_name_unique': True,
    'judge_rows': Judge.objects.count(), 'runtime_rows': RuntimeVersion.objects.count(),
    'migration_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                         for p in Path('/app/judge/migrations').glob('*.py')},
    'website_to_judge': 'NOT TESTED',
}, indent=2))
