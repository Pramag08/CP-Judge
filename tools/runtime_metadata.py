"""Non-secret versions from the isolated judge image; no problem data is read."""
import json
import platform
import subprocess
from pathlib import Path
import yaml

runtime = yaml.safe_load(Path('/judge-runtime-paths.yml').read_text())['runtime']
compilers = {}
for key in ['g++17', 'g++20', 'g++23']:
    command = runtime.get(key)
    if command:
        version = subprocess.run([command, '--version'], text=True, capture_output=True)
        macros = subprocess.run([command, '-std=c++' + key[-2:], '-dM', '-E', '-x', 'c++', '-'],
                                input='', text=True, capture_output=True)
        compilers[key] = {'command': command, 'version': version.stdout.splitlines()[0] if version.stdout else version.stderr,
                          'cplusplus': next((s.split()[-1] for s in macros.stdout.splitlines() if s.startswith('#define __cplusplus ')), None)}
print(json.dumps({'python': platform.python_version(), 'kernel': platform.release(),
                  'judge_commit': Path('/judge-source-commit').read_text().strip(),
                  'compilers': compilers,
                  'python_packages': subprocess.check_output(['/env/bin/python3', '-m', 'pip', 'freeze'], text=True).splitlines()}, indent=2))
