"""Replay A09 in disposable Docker services; installs nothing on the host."""
import argparse
import datetime
import json
import pathlib
import re
import secrets
import subprocess
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work-dir', type=pathlib.Path, required=True)
    parser.add_argument('--prefix', required=True)
    parser.add_argument('--image', default='cpjudge-a09-site:locked')
    args = parser.parse_args()
    if not re.fullmatch(r'[a-z][a-z0-9-]{2,45}', args.prefix):
        parser.error('prefix must contain 3–46 lowercase letters, digits or hyphens')
    root = args.work_dir.resolve()
    root.mkdir(parents=True, exist_ok=False)
    (root / 'logs').mkdir()
    private = root / 'private'
    private.mkdir(mode=0o700)
    here = pathlib.Path(__file__).resolve().parent
    pins = json.loads((here / 'base-pins.json').read_text())
    records = []

    def run(name, argv, *, input=None, expected=0):
        started = datetime.datetime.now(datetime.timezone.utc).isoformat()
        result = subprocess.run(argv, input=input, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (root / 'logs' / (name + '.log')).write_text(result.stdout)
        records.append(dict(name=name, argv=argv, started=started,
                            exit_status=result.returncode, expected_exit=expected,
                            log='logs/' + name + '.log'))
        (root / 'commands.json').write_text(json.dumps(records, indent=2) + '\n')
        print(name, 'exit', result.returncode, flush=True)
        if expected is not None and result.returncode != expected:
            raise RuntimeError(f'{name}: expected exit {expected}; see its log')
        return result

    network = args.prefix + '-net'
    db, redis, site = (args.prefix + suffix for suffix in ('-db', '-redis', '-site'))
    password = secrets.token_urlsafe(32)
    for filename, content in {
        'db.env': f'MARIADB_ROOT_PASSWORD={secrets.token_urlsafe(32)}\nMARIADB_DATABASE=a09\nMARIADB_USER=a09\nMARIADB_PASSWORD={password}\n',
        'site.env': f'A09_SECRET_KEY={secrets.token_urlsafe(64)}\nDB_PASSWORD={password}\nA09_LOGIN_PASSWORD={secrets.token_urlsafe(32)}\n',
    }.items():
        path = private / filename
        path.write_text(content)
        path.chmod(0o600)
    created = []
    network_created = False

    def manage(name, *command, expected=0):
        return run(name, ['docker', 'exec', site, 'python', 'manage.py', *command], expected=expected)

    def shell(name, code):
        return run(name, ['docker', 'exec', '-i', site, 'python', 'manage.py', 'shell'], input=code)

    try:
        # Refuse collisions; cleanup may remove only objects this process created.
        for name in (db, redis, site, network):
            probe = subprocess.run(['docker', 'inspect', name], capture_output=True)
            if probe.returncode == 0:
                raise RuntimeError('Docker object already exists: ' + name)
        run('network-create', ['docker', 'network', 'create', '--internal', '--label', 'secureexam.task=A09', network])
        network_created = True
        for name, alias, image, options, command in (
            (db, 'db', pins['mariadb'], ['--memory', '1536m', '--cpus', '2', '--tmpfs', '/var/lib/mysql:rw,size=1073741824', '--env-file', str(private / 'db.env')], []),
            (redis, 'redis', pins['redis'], ['--memory', '256m', '--tmpfs', '/data:rw,size=67108864'], ['redis-server', '--save', '', '--appendonly', 'no']),
            (site, 'site', args.image, ['--memory', '1536m', '--cpus', '2', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges', '--env-file', str(private / 'site.env')], ['sleep', 'infinity']),
        ):
            run(alias + '-start', ['docker', 'run', '-d', '--name', name, '--label', 'secureexam.task=A09', '--network', network, '--network-alias', alias, *options, image, *command])
            created.append(name)
        for _ in range(45):
            ready = subprocess.run(['docker', 'exec', db, 'healthcheck.sh', '--connect', '--innodb_initialized'], capture_output=True)
            if ready.returncode == 0:
                break
            time.sleep(1)
        run('db-ready', ['docker', 'exec', db, 'healthcheck.sh', '--connect', '--innodb_initialized'])
        run('pip-check', ['docker', 'exec', site, 'python', '-m', 'pip', 'check'])
        manage('system-check', 'check', '--database', 'default')
        manage('migrate', 'migrate', '--noinput')
        manage('migration-reapply', 'migrate', '--noinput')
        manage('no-pending-migrations', 'migrate', '--check')
        manage('fixtures', 'loaddata', 'navbar', 'language_small')
        shell('seed-and-versions', (here / 'seed.py').read_text())
        # Known failed supplemental diagnostic: never label it a passing check.
        manage('migration-drift-KNOWN-FAIL', 'makemigrations', '--check', '--dry-run', expected=1)
        shell('migration-state-audit', (here / 'migration_audit.py').read_text())
        shell('class-constraint-audit', "from django.db import connection\nwith connection.cursor() as c:\n    constraints=connection.introspection.get_constraints(c,'judge_class')\nfound={k:v for k,v in constraints.items() if v['columns']==['name'] and v['unique']}\nassert found\nprint(found)\n")
        manage('deployment-warnings', 'check', '--deploy')
        shell('unsilenced-checks', "from django.test import override_settings\nfrom django.core.management import call_command\nwith override_settings(SILENCED_SYSTEM_CHECKS=[]): call_command('check', databases=['default'])\n")
        grant = "GRANT ALL PRIVILEGES ON test_a09.* TO 'a09'@'%';\n"
        run('test-db-permission', ['docker', 'exec', '-i', db, 'sh', '-c', 'MYSQL_PWD="$MARIADB_ROOT_PASSWORD" mariadb -u root'], input=grant)
        tests = manage('upstream-tests', 'test', 'judge', '--noinput', '-v', '2')
        assert 'Ran 79 tests' in tests.stdout and '\nOK\n' in tests.stdout
        for command in (['compilemessages'], ['compilejsi18n'], ['collectstatic', '--noinput']):
            manage(command[0], *command)
        run('copy-http-probe', ['docker', 'cp', str(here / 'http_smoke.py'), site + ':/tmp/http_smoke.py'])
        run('http-start', ['docker', 'exec', '-d', site, 'sh', '-c', 'python manage.py runserver 0.0.0.0:8000 --noreload > /tmp/http.log 2>&1'])
        time.sleep(3)
        run('http-smoke', ['docker', 'exec', site, 'python', '/tmp/http_smoke.py'])
        run('celery-start', ['docker', 'exec', '-d', site, 'sh', '-c', 'celery -A dmoj_celery worker --pool=solo --concurrency=1 --loglevel=INFO --hostname=a09@site > /tmp/celery.log 2>&1'])
        time.sleep(3)
        run('celery-ping', ['docker', 'exec', site, 'celery', '-A', 'dmoj_celery', 'inspect', 'ping', '--timeout', '10'])
        shell('celery-demo-task', "from dmoj_celery import app\nresult=app.send_task('judge.tasks.demo.success')\nassert result.get(timeout=20) is None\nassert result.successful()\nprint('Upstream no-op task completed through Redis: SUCCESS')\n")
        # Dump contains only disposable seed data and remains inside the DB container.
        run('backup-restore', ['docker', 'exec', db, 'sh', '-ec', 'export MYSQL_PWD="$MARIADB_ROOT_PASSWORD"\nmariadb-dump -u root --single-transaction a09 > /tmp/a09.sql\nmariadb -u root -e "CREATE DATABASE a09_restore CHARACTER SET utf8mb4; GRANT ALL PRIVILEGES ON a09_restore.* TO \'a09\'@\'%\';"\nmariadb -u root a09_restore < /tmp/a09.sql'])
        run('restored-migrations', ['docker', 'exec', '-e', 'DB_NAME=a09_restore', site, 'python', 'manage.py', 'migrate', '--check'])
        run('restored-seed', ['docker', 'exec', '-e', 'DB_NAME=a09_restore', '-i', site, 'python', 'manage.py', 'shell'], input="import os\nfrom django.contrib.auth.models import User\nfrom judge.models import Language\nassert User.objects.get(username='a09-smoke').check_password(os.environ['A09_LOGIN_PASSWORD'])\nassert Language.objects.get(key='CPP23').extension=='cpp'\nprint('Restored user password and CPP23 metadata verified')\n")
        run('live-isolation', ['docker', 'inspect', *created, '--format', '{{json .Name}} {{json .HostConfig.NetworkMode}} {{json .HostConfig.PortBindings}} {{json .Config.User}} {{json .HostConfig.Tmpfs}} {{json .HostConfig.CapDrop}} {{json .HostConfig.SecurityOpt}}'])
        run('network-isolation', ['docker', 'network', 'inspect', network, '--format', '{{json .Internal}}'])
        run('image-identity', ['docker', 'image', 'inspect', args.image, '--format', '{{json .Id}} {{json .RepoDigests}}'])
        (root / 'result.json').write_text(json.dumps({'status': 'PASS', 'scope': 'A09 supported-stack startup only', 'known_failed_diagnostic': 'makemigrations --check --dry-run: 11 metadata-only alterations, no DDL', 'website_to_judge': 'NOT TESTED'}, indent=2) + '\n')
    finally:
        for name in created:
            if name == site:
                for filename in ('http', 'celery'):
                    run(filename + '-log', ['docker', 'exec', site, 'cat', '/tmp/' + filename + '.log'], expected=None)
            else:
                run(name.rsplit('-', 1)[-1] + '-log', ['docker', 'logs', name], expected=None)
        if created:
            run('cleanup-containers', ['docker', 'rm', '-f', '-v', *created], expected=None)
        if network_created:
            run('cleanup-network', ['docker', 'network', 'rm', network], expected=None)


if __name__ == '__main__':
    main()
