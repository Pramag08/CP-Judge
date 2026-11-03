import json
from django.apps import apps
from django.db import connection
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.state import ProjectState
from django.db.migrations.autodetector import MigrationAutodetector
loader=MigrationLoader(connection)
old=loader.project_state(); new=ProjectState.from_apps(apps)
changes=MigrationAutodetector(old,new).changes(graph=loader.graph)
rows=[]; sql=[]
for label,migrations in changes.items():
    for migration in migrations:
        for operation in migration.operations:
            assert operation.__class__.__name__=='AlterField',operation
            key=(label,operation.model_name)
            prev=old.models[key].fields[operation.name]
            oldargs=prev.deconstruct();newargs=operation.field.deconstruct()
            changed=sorted(k for k in set(oldargs[3])|set(newargs[3]) if oldargs[3].get(k)!=newargs[3].get(k))
            rows.append({'model':operation.model_name,'field':operation.name,'changed_options':changed})
        with connection.schema_editor(collect_sql=True,atomic=False) as editor:
            migration.apply(old.clone(),editor,collect_sql=True)
        sql.extend(editor.collected_sql)
statements=[s for s in sql if not s.lstrip().startswith('--')]
assert not statements,statements
assert len(rows)==11,rows
assert all(set(row['changed_options']) <= {'related_name','validators','choices','verbose_name','help_text'} for row in rows)
print(json.dumps({'alter_fields':rows,'collected_sql':sql,'database_changing_statements':statements,'conclusion':'11 upstream model-state differences; no database DDL generated on MariaDB 11.4.13. No migration file or schema change made.'},indent=2))
