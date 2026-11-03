"""Copy an exact clean upstream checkout into a fresh A09 Docker context."""
import argparse
import hashlib
import json
import pathlib
import shutil
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source', type=pathlib.Path, required=True)
parser.add_argument('--output', type=pathlib.Path, required=True)
args = parser.parse_args()
here = pathlib.Path(__file__).resolve().parent
pin = json.loads((here / 'source-pin.json').read_text())
source = args.source.resolve()


def git(*argv):
    return subprocess.check_output(['git', '-C', str(source), *argv], text=True).strip()


assert git('rev-parse', 'HEAD') == pin['commit']
assert not git('status', '--porcelain'), 'upstream source must be clean'
assert git('-C', 'resources/libs', 'rev-parse', 'HEAD') == pin['asset_commit']
assert hashlib.sha256((source / 'LICENSE').read_bytes()).hexdigest() == pin['license_sha256']
args.output.mkdir(parents=True, exist_ok=False)
shutil.copytree(source, args.output / 'site', ignore=shutil.ignore_patterns('.git', '__pycache__', '*.pyc'))
for filename in ('Dockerfile', 'requirements.in', 'requirements.lock', 'package.json',
                 'package-lock.json', 'local_settings.py', '.dockerignore'):
    shutil.copy2(here / filename, args.output / filename)
print('Prepared pinned source/assets and lockfiles:', args.output)
