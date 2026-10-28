"""Fetch only the pinned converter; never run its installer or imported code."""
import json
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[1]
dep = json.loads((root / 'dependencies.json').read_text())['converter']
target = root / '.deps' / 'converter'
if not target.exists():
    subprocess.run(['git', 'clone', dep['url'], str(target)], check=True)
subprocess.run(['git', '-C', str(target), 'checkout', '--detach', dep['commit']], check=True)
