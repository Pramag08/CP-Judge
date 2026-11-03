"""Lifecycle of C11's private verifier in the EXISTING pinned worker container."""
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
WORKER = 'cpjudge-b03-worker'
IMAGE = 'sha256:d8d9dded026cd9d2d4a4f41136b99fa935935f8638cab314ad0a0e567ebcf0e8'
SCAN = '''import os,signal,sys
from pathlib import Path
found=[]
for p in Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:args=(p/'cmdline').read_bytes().split(b'\\0')
 except OSError:continue
 if args[1:2]==[b'/tmp/c11_worker.py'] or args[1:3]==[b'-B',b'/tmp/c11_worker.py']:
  found.append(int(p.name))
  if sys.argv[1]=='stop':os.kill(int(p.name),signal.SIGTERM)
assert len(found)<=1
print(len(found))
'''


def docker(*args):
    return subprocess.check_output(['docker', *args])


def main(mode):
    if not (ROOT/'build/phase-c-c11-1/enabled').exists():
        return
    assert docker('inspect', WORKER, '--format', '{{.Image}}').decode().strip() == IMAGE
    count = int(docker('exec', WORKER, '/env/bin/python3', '-c', SCAN, mode))
    if mode == 'stop':
        return
    if count:
        print('C11 verifier already running.');return
    for source, target in ((ROOT/'deploy/phase-c/c11_worker.py', '/tmp/c11_worker.py'),
                           (ROOT/'deploy/phase-c/cpjudge/readiness_wire.py', '/tmp/readiness_wire.py')):
        subprocess.run(['docker','exec','-i',WORKER,'/env/bin/python3','-c',
            "import sys;from pathlib import Path;p=Path(sys.argv[1]);p.write_bytes(sys.stdin.buffer.read());p.chmod(0o600)",target],
            input=source.read_bytes(),check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    docker('exec', '-d', WORKER, '/bin/bash', '-c',
           '. ~judge/.profile; export HOME=/tmp; exec /env/bin/python3 -B /tmp/c11_worker.py > /tmp/c11-readiness.log 2>&1')
    for _ in range(40):
        # Read only service socket readiness, without creating malformed native
        # bridge connections or exposing worker keys to this operator command.
        result = subprocess.run(['docker','exec',WORKER,'/env/bin/python3','-c',
            "import socket;s=socket.create_connection(('127.0.0.1',9994),timeout=1);s.close()"],capture_output=True)
        if result.returncode == 0:
            print('C11 private worker verifier listening.');return
        time.sleep(0.5)
    raise RuntimeError('C11 verifier failed to start; inspect private worker log')


if __name__ == '__main__':
    main(sys.argv[1])
