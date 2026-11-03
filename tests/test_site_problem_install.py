import os
from pathlib import Path
import tempfile
import unittest

from tools.site_problem import canonical_digest, file_manifest, install_directory


class ImmutableInstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        (self.source / 'init.yml').write_text('archive: data.zip\n')
        (self.source / 'data.zip').write_bytes(b'original private bytes')
        self.parent = self.root / 'installed'
        self.code = 'pv000000000000000001'
        self.manifest = file_manifest(self.source)

    def tearDown(self):
        for directory, _, _ in os.walk(self.root):
            Path(directory).chmod(0o700)
        self.temp.cleanup()

    def test_repeat_preserves_inode_mtime_and_bytes(self):
        self.assertTrue(install_directory(self.source, self.parent, self.code, self.manifest))
        before = (self.parent / self.code / 'data.zip').stat()
        self.assertFalse(install_directory(self.source, self.parent, self.code, self.manifest))
        after = (self.parent / self.code / 'data.zip').stat()
        self.assertEqual((before.st_ino, before.st_mtime_ns), (after.st_ino, after.st_mtime_ns))
        self.assertEqual(file_manifest(self.parent / self.code), self.manifest)
        self.assertEqual(after.st_mode & 0o222, 0)

    def test_same_code_different_bytes_refused_without_replacement(self):
        install_directory(self.source, self.parent, self.code, self.manifest)
        (self.source / 'data.zip').write_bytes(b'different version')
        with self.assertRaisesRegex(AssertionError, 'differs'):
            install_directory(self.source, self.parent, self.code, file_manifest(self.source))
        self.assertEqual((self.parent / self.code / 'data.zip').read_bytes(), b'original private bytes')

    def test_stale_expected_manifest_refused_before_staging(self):
        (self.source / 'data.zip').write_bytes(b'tampered staging input')
        with self.assertRaises(AssertionError):
            install_directory(self.source, self.parent, self.code, self.manifest)
        self.assertFalse((self.parent / self.code).exists())

    def test_symlink_input_refused(self):
        (self.source / 'escape').symlink_to('/etc/passwd')
        with self.assertRaisesRegex(AssertionError, 'Symlinks'):
            file_manifest(self.source)

    def test_symlink_destination_parent_refused(self):
        other = self.root / 'other'
        other.mkdir()
        self.parent.symlink_to(other, target_is_directory=True)
        with self.assertRaisesRegex(AssertionError, 'parent'):
            install_directory(self.source, self.parent, self.code, self.manifest)
        self.assertEqual(list(other.iterdir()), [])

    def test_metadata_changes_full_digest(self):
        first = {'files': self.manifest, 'time_limit': 2.0, 'language': 'CPP23'}
        second = dict(first, time_limit=1.0)
        self.assertNotEqual(canonical_digest(first), canonical_digest(second))


if __name__ == '__main__':
    unittest.main()
