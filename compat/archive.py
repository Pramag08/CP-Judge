"""Bounded ZIP extraction. This module never executes archive contents."""
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
import re
import stat
import struct
import unicodedata
import zipfile


class ArchiveRejected(ValueError):
    pass


@dataclass(frozen=True)
class ArchiveLimits:
    upload_bytes: int = 256 * 1024**2
    entries: int = 10000
    member_bytes: int = 256 * 1024**2
    expanded_bytes: int = 1024**3
    ratio: int = 1000

    def __post_init__(self):
        if any(type(v) is not int or v <= 0 for v in vars(self).values()):
            raise ValueError('Archive limits must be positive integers')


def member_path(name):
    if not name or '\\' in name or ':' in name or any(ord(c) < 32 or ord(c) == 127 for c in name):
        raise ArchiveRejected('Unsafe archive path')
    path = PurePosixPath(name)
    raw = name[:-1] if name.endswith('/') else name
    parts = raw.split('/')
    if path.is_absolute() or any(p in ('', '.', '..') or p.endswith((' ', '.')) for p in parts):
        raise ArchiveRejected('Absolute, traversal or ambiguous archive path')
    if len(name.encode('utf-8')) > 4096 or len(parts) > 32:
        raise ArchiveRejected('Archive path exceeds length/depth limit')
    if any(re.fullmatch(r'(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?', p, re.I) for p in parts):
        raise ArchiveRejected('Reserved archive path')
    return path


def preflight_directory(archive, limits):
    """Bound central-directory work before ZipFile allocates all ZipInfo objects."""
    size = archive.stat().st_size
    with archive.open('rb') as source:
        source.seek(max(0, size - 65557))
        tail_start = source.tell()
        tail = source.read(65557)
        index = tail.rfind(b'PK\x05\x06')
        if index < 0 or len(tail) - index < 22:
            raise ArchiveRejected('Invalid ZIP end record')
        _, disk, directory_disk, disk_count, count, directory_size, offset, comment = struct.unpack(
            '<4s4H2LH', tail[index:index + 22])
        if index + 22 + comment != len(tail):
            raise ArchiveRejected('Ambiguous ZIP end record or trailing data')
        if (disk or directory_disk or disk_count != count or count == 0xffff
                or directory_size == 0xffffffff or offset == 0xffffffff):
            raise ArchiveRejected('Multi-disk and ZIP64 packages are unsupported')
        if count > limits.entries:
            raise ArchiveRejected('ZIP exceeds entry count limit')
        end = tail_start + index
        if offset + directory_size != end:
            raise ArchiveRejected('ZIP central-directory bounds mismatch')
        source.seek(offset)
        actual = 0
        while source.tell() < end:
            actual += 1
            if actual > limits.entries:
                raise ArchiveRejected('Actual ZIP entry count exceeds limit')
            header = source.read(46)
            if len(header) != 46 or header[:4] != b'PK\x01\x02':
                raise ArchiveRejected('Invalid ZIP directory entry')
            compressed, expanded = struct.unpack('<LL', header[20:28])
            if expanded > max(compressed, 1) * limits.ratio:
                raise ArchiveRejected(
                    f'ZIP entry ratio exceeded: {actual} {expanded} {compressed} {limits.ratio}')
            name_size, extra_size, comment_size = struct.unpack('<3H', header[28:34])
            if name_size > 4096:
                raise ArchiveRejected('ZIP member name exceeds path limit')
            following = source.tell() + name_size + extra_size + comment_size
            if following > end:
                raise ArchiveRejected('ZIP directory entry exceeds bounds')
            source.seek(following)
        if actual != count:
            raise ArchiveRejected('ZIP declared/actual entry count mismatch')


def extract_zip(archive, target, limits=None):
    limits = limits or ArchiveLimits()
    archive, target = Path(archive), Path(target)
    if archive.stat().st_size > limits.upload_bytes:
        raise ArchiveRejected('ZIP exceeds upload byte limit')
    if target.is_symlink() or (target.exists() and (not target.is_dir() or any(target.iterdir()))):
        raise ArchiveRejected('Extraction requires a new, empty private directory')
    preflight_directory(archive, limits)
    target.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        with zipfile.ZipFile(archive) as z:
            members = z.infolist()
            if len(members) > limits.entries:
                raise ArchiveRejected('ZIP exceeds entry count limit')
            seen, files, paths, metadata_total = set(), set(), [], 0
            spellings = {}
            for info in members:
                if info.orig_filename != info.filename:
                    raise ArchiveRejected('Truncated or ambiguous ZIP filename')
                path = member_path(info.filename)
                for ancestor in [path, *path.parents]:
                    if str(ancestor) == '.':
                        continue
                    spelling = ancestor.as_posix()
                    folded = unicodedata.normalize('NFC', spelling).casefold()
                    if folded in spellings and spellings[folded] != spelling:
                        raise ArchiveRejected('Ambiguous archive directory spelling')
                    spellings[folded] = spelling
                key = unicodedata.normalize('NFC', path.as_posix()).casefold()
                if key in seen:
                    raise ArchiveRejected('Duplicate or ambiguous archive path')
                seen.add(key)
                mode = info.external_attr >> 16
                kind = stat.S_IFMT(mode)
                if kind not in (0, stat.S_IFDIR if info.is_dir() else stat.S_IFREG):
                    raise ArchiveRejected('Symlinks and special archive entries are forbidden')
                if info.flag_bits & 1:
                    raise ArchiveRejected('Encrypted archive entries are unsupported')
                if info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
                    raise ArchiveRejected('Unsupported ZIP compression method')
                metadata_total += info.file_size
                if info.file_size > limits.member_bytes or metadata_total > limits.expanded_bytes:
                    raise ArchiveRejected('ZIP exceeds expansion/ratio limit')
                if info.file_size > max(info.compress_size, 1) * limits.ratio:
                    # Numeric metadata only: never put a private member name in a
                    # public-facing conversion error.
                    raise ArchiveRejected(
                        f'ZIP entry ratio exceeded: {len(paths) + 1} {info.file_size} '
                        f'{info.compress_size} {limits.ratio}')
                if not info.is_dir():
                    files.add(key)
                paths.append((info, path, key))
            for info, path, key in paths:
                if any(unicodedata.normalize('NFC', p.as_posix()).casefold() in files for p in path.parents if str(p) != '.'):
                    raise ArchiveRejected('File/directory archive path conflict')
            total = 0
            for info, path, _ in paths:
                output = target.joinpath(*path.parts)
                if info.is_dir():
                    output.mkdir(parents=True, exist_ok=True, mode=0o700)
                    continue
                output.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                size = 0
                # Exclusive creation; never replace an existing path or follow a link.
                with z.open(info) as src, output.open('xb') as dst:
                    output.chmod(0o600)
                    while True:
                        chunk = src.read(min(65536, limits.member_bytes - size + 1,
                                             limits.expanded_bytes - total + 1))
                        if not chunk:
                            break
                        size += len(chunk)
                        total += len(chunk)
                        if (size > limits.member_bytes or total > limits.expanded_bytes
                                or size > max(info.compress_size, 1) * limits.ratio):
                            raise ArchiveRejected('Actual extracted bytes exceed expansion limit')
                        dst.write(chunk)
                if size != info.file_size:
                    raise ArchiveRejected('ZIP declared/actual member size mismatch')
            return {'entries':len(members), 'expanded_bytes':total}
    except (zipfile.BadZipFile, NotImplementedError, RuntimeError) as exc:
        raise ArchiveRejected('Invalid or unsupported ZIP archive') from exc
