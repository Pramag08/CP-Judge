"""Immutable operator-install helpers. No conversion, publication or execution."""
import ctypes
import errno
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile


def file_manifest(root):
    root = Path(root)
    assert root.is_dir() and not root.is_symlink()
    files = []
    for path in sorted(root.rglob('*')):
        assert not path.is_symlink(), 'Symlinks are not an installation input'
        if path.is_file():
            digest = hashlib.sha256()
            with path.open('rb') as source:
                for chunk in iter(lambda: source.read(1024 * 1024), b''):
                    digest.update(chunk)
            files.append({'path': path.relative_to(root).as_posix(), 'size': path.stat().st_size,
                          'sha256': digest.hexdigest()})
        else:
            assert path.is_dir(), 'Special files are not an installation input'
    return files


def canonical_digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()).hexdigest()


def install_directory(source, parent, code, expected, *, durable=False):
    """Never overwrite. Stage/verify then Linux atomic rename with NOREPLACE."""
    source, parent = Path(source), Path(parent)
    assert len(code) == 20 and code.startswith('pv') and code[2:].isdigit()
    assert file_manifest(source) == expected
    assert not parent.is_symlink(), 'Installation parent must not be a symlink'
    parent.mkdir(parents=True, exist_ok=True)
    destination = parent / code
    if destination.exists():
        assert file_manifest(destination) == expected, 'Immutable installed directory differs'
        return False
    stage = Path(tempfile.mkdtemp(prefix='.' + code + '-', dir=parent))
    try:
        shutil.copytree(source, stage, dirs_exist_ok=True)
        assert file_manifest(stage) == expected
        for p in stage.rglob('*'):
            p.chmod(0o555 if p.is_dir() else 0o444)
        stage.chmod(0o555)
        if durable:
            # C10 requires file data and rename ordering to survive process loss.
            for p in stage.rglob('*'):
                if p.is_file():
                    with p.open('rb') as f:os.fsync(f.fileno())
            for p in sorted([stage,*[p for p in stage.rglob('*') if p.is_dir()]], key=lambda p:len(p.parts), reverse=True):
                fd=os.open(p,os.O_RDONLY|os.O_DIRECTORY)
                try:os.fsync(fd)
                finally:os.close(fd)
        libc = ctypes.CDLL(None, use_errno=True)
        rename = libc.renameat2
        rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
        rename.restype = ctypes.c_int
        if rename(-100, os.fsencode(stage), -100, os.fsencode(destination), 1) != 0:
            number = ctypes.get_errno()
            if number == errno.EEXIST:
                assert file_manifest(destination) == expected, 'Concurrent conflicting installation'
                return False
            raise OSError(number, os.strerror(number))
        if durable:
            fd=os.open(parent,os.O_RDONLY|os.O_DIRECTORY)
            try:os.fsync(fd)
            finally:os.close(fd)
        return True
    finally:
        if stage.exists():
            for p in stage.rglob('*'):
                if p.is_dir():
                    p.chmod(0o700)
            stage.chmod(0o700)
            shutil.rmtree(stage)
