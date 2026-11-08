import io
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch
import zipfile
from compat.archive import ArchiveLimits, ArchiveRejected, extract_zip, preflight_directory


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.archive = self.root / 'package.zip'
        self.target = self.root / 'extract'

    def make(self, entries, compression=zipfile.ZIP_STORED):
        with zipfile.ZipFile(self.archive, 'w', compression=compression) as z:
            for name, data in entries:
                z.writestr(name, data)

    def reject(self, members, **limits):
        self.make(members)
        with self.assertRaises(ArchiveRejected):
            extract_zip(self.archive, self.target, ArchiveLimits(**limits))

    def test_valid_local_assets_and_unicode(self):
        self.make([('problem.xml', b'<problem/>'), ('images/', b''), ('images/diagram.png', b'image'), ('notes/é.txt', b'text')])
        self.assertEqual(extract_zip(self.archive, self.target), {'entries':4,'expanded_bytes':19})
        self.assertEqual((self.target / 'images/diagram.png').read_bytes(), b'image')

    def test_absolute_traversal_and_ambiguous_paths(self):
        for name in ('../escape','/absolute','C:/drive','a\\b','a/../b','a//b','./file','a./x','x /y','nul.txt','x\x00y'):
            with self.subTest(name=name):
                # zipfile truncates NUL paths on writing; member_path is checked directly.
                from compat.archive import member_path
                with self.assertRaises(ArchiveRejected):
                    member_path(name)

    def test_case_and_unicode_collisions(self):
        for entries in ([('A','1'),('a','2')], [('é','1'),('e\u0301','2')], [('x','1'),('x','2')]):
            with self.subTest(entries=entries):
                self.reject(entries)

    def test_symlink_and_device(self):
        for kind in (stat.S_IFLNK, stat.S_IFCHR, stat.S_IFIFO):
            info = zipfile.ZipInfo('link')
            info.create_system = 3
            info.external_attr = (kind | 0o777) << 16
            self.reject([(info,'/etc/passwd')])

    def test_implicit_directory_case_collisions(self):
        self.reject([('A/x','1'),('a/y','2')])

    def test_destination_regular_file_rejected(self):
        self.target.write_bytes(b'original')
        self.make([('a','data')])
        with self.assertRaises(ArchiveRejected):
            extract_zip(self.archive,self.target)
        self.assertEqual(self.target.read_bytes(),b'original')

    def test_path_prefix_conflict(self):
        self.reject([('file','x'),('file/child','x')])

    def test_metadata_limits(self):
        self.reject([('a','123'),('b','456')], entries=1)
        self.reject([('a','123')], member_bytes=2)
        self.reject([('a','123'),('b','456')], expanded_bytes=5)
        self.reject([('a','123')], upload_bytes=1)

    def test_lied_entry_count_rejected_before_zipinfo_allocation(self):
        import struct
        self.make([('a','1'),('b','2')])
        data=bytearray(self.archive.read_bytes())
        end=data.rfind(b'PK\x05\x06')
        struct.pack_into('<HH',data,end+8,0,0)
        self.archive.write_bytes(data)
        with patch('zipfile.ZipFile',side_effect=AssertionError('Should reject before parsing')):
            with self.assertRaises(ArchiveRejected):
                extract_zip(self.archive,self.target,ArchiveLimits(entries=1))

    def test_bomb_ratio(self):
        self.make([('bomb',b'0'*100000)], zipfile.ZIP_DEFLATED)
        with self.assertRaisesRegex(ArchiveRejected, r'ZIP entry ratio exceeded: 1 100000 [0-9]+ 10'):
            extract_zip(self.archive, self.target, ArchiveLimits(ratio=10))

    def test_preflight_rejects_declared_ratio_above_1200_before_zipinfo(self):
        import struct
        self.make([('a',b'x')])
        data=bytearray(self.archive.read_bytes())
        directory=data.index(b'PK\x01\x02')
        struct.pack_into('<L',data,directory+24,1201)
        self.archive.write_bytes(data)
        with patch('zipfile.ZipFile',side_effect=AssertionError('Should reject before ZipInfo allocation')):
            with self.assertRaisesRegex(ArchiveRejected,r'ZIP entry ratio exceeded: 1 1201 1 1200'):
                extract_zip(self.archive,self.target,ArchiveLimits(ratio=1200))

    def test_preflight_accepts_declared_ratio_at_1200(self):
        import struct
        self.make([('a',b'x')])
        data=bytearray(self.archive.read_bytes())
        directory=data.index(b'PK\x01\x02')
        struct.pack_into('<L',data,directory+24,1200)
        self.archive.write_bytes(data)
        preflight_directory(self.archive,ArchiveLimits(ratio=1200))

    def test_actual_stream_limits_even_if_metadata_lies(self):
        self.make([('a','x')])
        with patch.object(zipfile.ZipFile, 'open', return_value=io.BytesIO(b'X'*100)):
            with self.assertRaisesRegex(ArchiveRejected, 'Actual extracted bytes'):
                extract_zip(self.archive, self.target, ArchiveLimits(member_bytes=8))
        self.assertLessEqual((self.target/'a').stat().st_size, 8)

    def test_actual_aggregate_limit_even_if_metadata_lies(self):
        self.make([('a','1234'),('b','1')])
        with patch.object(zipfile.ZipFile, 'open', side_effect=[io.BytesIO(b'1234'),io.BytesIO(b'5678')]):
            with self.assertRaisesRegex(ArchiveRejected, 'Actual extracted bytes'):
                extract_zip(self.archive, self.target, ArchiveLimits(expanded_bytes=6))

    def test_actual_ratio_limit_even_if_metadata_lies(self):
        self.make([('a','x')])
        with patch.object(zipfile.ZipFile,'open',return_value=io.BytesIO(b'X'*100)):
            with self.assertRaisesRegex(ArchiveRejected,'Actual extracted bytes'):
                extract_zip(self.archive,self.target,ArchiveLimits(ratio=5))

    def test_actual_ratio_above_1200_rejected_even_if_metadata_passes(self):
        self.make([('a',b'x')])
        with patch.object(zipfile.ZipFile,'open',return_value=io.BytesIO(b'X'*1201)):
            with self.assertRaisesRegex(ArchiveRejected,'Actual extracted bytes'):
                extract_zip(self.archive,self.target,ArchiveLimits(ratio=1200))
        self.assertEqual((self.target/'a').stat().st_size,0)

    def test_destination_must_be_empty_and_not_symlink(self):
        self.make([('a','content')])
        self.target.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(ArchiveRejected):
            extract_zip(self.archive, self.target)

    def test_destination_existing_file_preserved(self):
        self.target.mkdir()
        (self.target/'a').write_text('original')
        self.make([('a','replacement')])
        with self.assertRaises(ArchiveRejected):
            extract_zip(self.archive, self.target)
        self.assertEqual((self.target/'a').read_text(), 'original')

    def test_bad_zip(self):
        self.archive.write_bytes(b'not a zip')
        with self.assertRaises(ArchiveRejected):
            extract_zip(self.archive, self.target)

    def test_unsupported_compression_encryption_and_multidisk(self):
        import struct
        self.make([('file','data')],zipfile.ZIP_BZIP2)
        with self.assertRaises(ArchiveRejected):extract_zip(self.archive,self.target)
        for mode in ('encrypted','multidisk','zip64'):
            self.make([('file','data')])
            data=bytearray(self.archive.read_bytes())
            if mode=='encrypted':
                offset=data.index(b'PK\x01\x02')
                struct.pack_into('<H',data,offset+8,1)
            else:
                offset=data.rfind(b'PK\x05\x06')
                struct.pack_into('<H',data,offset+(4 if mode=='multidisk' else 10),1 if mode=='multidisk' else 0xffff)
            self.archive.write_bytes(data)
            with self.assertRaises(ArchiveRejected):extract_zip(self.archive,self.target)

    def test_invalid_limits(self):
        with self.assertRaises(ValueError):
            ArchiveLimits(entries=0)
