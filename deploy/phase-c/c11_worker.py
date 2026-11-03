"""Trusted C11 verifier in the initial pinned worker, on a private loopback channel.

Reads installed bytes only. No submitted code, checker, conversion or problem
probe is executed. Native executor startup self-tests are retained. Secrets never
leave this supervisor and are not made available to submitted-program sandboxes.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import socketserver
import stat
import sys
import time

try:
    from cpjudge import readiness_wire as wire
except ModuleNotFoundError:
    import readiness_wire as wire

SOURCE_PIN = '1245dc4158dbb9e906c4c103e1ea939e012ee79b'
EXECUTORS = ['CPP11', 'CPP14', 'CPP17', 'CPP20', 'CPP23']


def file_hash(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            result.update(chunk)
    return result.hexdigest()


def installed_files(code, parent=Path('/problems')):
    if not re.fullmatch(r'pv[0-9]{18}', code):
        raise ValueError('Unrecognized immutable version code')
    root = parent/code
    if parent.is_symlink() or root.is_symlink() or not root.is_dir():
        raise ValueError('Version missing')
    if root.stat().st_mode & 0o222:
        raise ValueError('Version is not immutable')
    files = []
    size = 0
    for folder, dirs, names in os.walk(root, followlinks=False):
        for name in dirs+names:
            path = Path(folder)/name
            info = path.lstat()
            if stat.S_ISLNK(info.st_mode) or info.st_mode & 0o222:
                raise ValueError('Mutable or linked version data')
            if stat.S_ISDIR(info.st_mode):
                continue
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise ValueError('Unsupported version data')
            size += info.st_size
            if len(files) >= 4096 or size > 2*1024**3:
                raise ValueError('Verification bound exceeded')
            # O_NOFOLLOW also closes a leaf replacement race. Directory changes by
            # a privileged operator are outside the immutable-install trust model.
            fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
            with os.fdopen(fd, 'rb') as stream:
                before = os.fstat(stream.fileno())
                sha = hashlib.sha256()
                for chunk in iter(lambda: stream.read(1024*1024), b''):
                    sha.update(chunk)
                after = os.fstat(stream.fileno())
            if (before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
                    after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns):
                raise ValueError('Version changed during verification')
            files.append({'path': path.relative_to(root).as_posix(), 'size': after.st_size, 'sha256': sha.hexdigest()})
    return sorted(files, key=lambda row: row['path'])


def owns_native_connection(port, proc=Path('/proc')):
    # PID 1 is the existing native dmoj supervisor, not this verifier. Match its
    # actual socket inode and local TCP port to this bridge's authenticated peer.
    argv = (proc/'1/cmdline').read_bytes().split(b'\0')
    # The pinned supervisor uses setproctitle after startup. Require its actual
    # interpreter AND native title/argv AND owned authenticated TCP socket.
    titled = bool(argv and re.fullmatch(rb'DMOJ Judge [^ ]+ on 127\.0\.0\.1:9999', argv[0]))
    if (b'/env/bin/dmoj' not in argv and not titled) or (proc/'1/exe').resolve() != Path(sys.executable).resolve():
        return False
    inodes = set()
    for path in (proc/'1/fd').iterdir():
        try:
            target = os.readlink(path)
        except OSError:
            continue
        match = re.fullmatch(r'socket:\[(\d+)\]', target)
        if match:
            inodes.add(match.group(1))
    for name in ('tcp', 'tcp6'):
        for line in (proc/'net'/name).read_text().splitlines()[1:]:
            cells = line.split()
            if (int(cells[1].split(':')[1], 16) == port and
                    int(cells[2].split(':')[1], 16) == 9999 and
                    cells[3] == '01' and cells[9] in inodes):
                return True
    return False


def load_native():
    from dmoj import judgeenv, executors
    sys.argv = ['c11-readiness', '-c', '/config.yml', '--only-executors', ','.join(EXECUTORS), '--no-ansi']
    judgeenv.load_env(cli=True)
    if judgeenv.api_listen is not None or list(judgeenv.env.problem_storage_globs) != ['/problems/*']:
        raise ValueError('Unapproved native storage/API configuration')
    executors.load_executors()
    if set(executors.executors) != set(EXECUTORS):
        raise ValueError('Required native executors unavailable')
    return judgeenv, executors


def inventory(native):
    judgeenv, executors = native
    if Path('/judge-source-commit').read_text().strip() != SOURCE_PIN:
        raise ValueError('Worker source pin changed')
    runtime = {}
    for key in EXECUTORS:
        cls = executors.executors[key].Executor
        command = Path(cls.get_command()).resolve(strict=True)
        runtime[key] = {'versions': cls.get_runtime_versions(), 'command_sha256': file_hash(command),
                        'executor_sha256': file_hash(Path('/judge/dmoj/executors')/(key+'.py'))}
    return json.loads(wire.canonical({'source_pin': SOURCE_PIN, 'config_sha256': file_hash('/config.yml'),
        'runtime': runtime}))


def verify(body, native, baseline):
    if (body.get('schema') != 1 or not isinstance(body.get('nonce'), str) or len(body['nonce']) != 64 or
            not isinstance(body.get('connection'), str) or len(body['connection']) != 64 or
            abs(time.time()-body.get('issued', 0)) > 15):
        raise ValueError('Stale readiness challenge')
    if not owns_native_connection(body['peer_port']):
        raise ValueError('Native authenticated connection unavailable')
    current = inventory(native)
    if current != baseline or body['inventory'] != current:
        raise ValueError('Worker runtime/configuration changed')
    required = body['required']
    if not required or any(key not in current['runtime'] for key in required):
        raise ValueError('Required executor unavailable')
    # Hash every installed file anew, not advertisement/mtime or a copied receipt.
    actual = installed_files(body['code'])
    if actual != body['files']:
        raise ValueError('Installed version digest mismatch')
    if not owns_native_connection(body['peer_port']):
        raise ValueError('Native connection changed during verification')
    return {'schema': 1, 'request_digest': wire.digest(body), 'ok': True,
            'connection': body['connection'], 'nonce': body['nonce'], 'manifest_digest': body['manifest_digest']}


def main():
    native = load_native()
    baseline = inventory(native)
    if len(sys.argv) > 1 and '--inventory' in ORIGINAL_ARGS:
        print('C11_INVENTORY='+json.dumps(baseline));return
    key = native[0].env.key
    class Handler(socketserver.BaseRequestHandler):
        def handle(self):
            self.request.settimeout(8)
            try:
                body = wire.unseal(wire.read_frame(self.request), key)
            except Exception:
                return  # unauthenticated callers receive no information
            try:
                reply = verify(body, native, baseline)
            except Exception as exc:
                print('C11 verification denied: '+type(exc).__name__+': '+str(exc), file=sys.stderr, flush=True)
                reply = {'schema': 1, 'request_digest': wire.digest(body), 'ok': False}
            wire.write_frame(self.request, wire.seal(reply, key))
    class Server(socketserver.TCPServer):
        allow_reuse_address = True
    with Server(wire.ADDRESS, Handler) as server:
        server.serve_forever(poll_interval=0.5)


if __name__ == '__main__':
    ORIGINAL_ARGS = sys.argv[:]
    main()
