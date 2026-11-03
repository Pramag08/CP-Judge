"""C12 upload races against real native database connections and private files."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier, Lock
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import close_old_connections, connection
from django.test import TransactionTestCase

from cpjudge.imports import upload
from cpjudge.integration_tests import NativeUploadHTTPTests
from cpjudge.models import ImportJob


class UploadRaceTests(TransactionTestCase):
    setUp = NativeUploadHTTPTests.setUp
    zip_bytes = NativeUploadHTTPTests.zip_bytes

    def race(self, owners):
        from compat.archive import preflight_directory
        barrier = Barrier(len(owners))
        lock = Lock()
        staged = []
        connections = []
        data = self.zip_bytes()

        def overlap(path, limits):
            result = preflight_directory(path, limits)
            with lock:
                staged.append(path)
                with connection.cursor() as cursor:
                    cursor.execute('SELECT CONNECTION_ID()')
                    connections.append(cursor.fetchone()[0])
            # Every request has written a distinct complete archive before any
            # insertion starts. Neither storage nor database writes are mocked.
            barrier.wait(timeout=20)
            return result

        def store(owner):
            close_old_connections()
            try:
                job = upload(self.users[owner], SimpleUploadedFile('race.zip', data),
                             self.contests['c5a' if owner == 'C5A' else 'c5b'],
                             validate_archive=True)
                return job.pk
            finally:
                connection.close()

        with patch('compat.archive.preflight_directory', side_effect=overlap):
            with ThreadPoolExecutor(max_workers=len(owners)) as pool:
                ids = list(pool.map(store, owners))
        self.assertEqual(len(set(connections)), len(owners))
        self.assertEqual(len(set(staged)), len(owners))
        self.assertEqual(set(Path(self.temp.name).glob('*.zip')),
                         {Path(self.temp.name) / key for key in
                          ImportJob.objects.values_list('archive_key', flat=True)})
        return ids

    def test_six_concurrent_same_owner_uploads_keep_one_archive(self):
        ids = self.race(['C5A'] * 6)
        self.assertEqual(len(set(ids)), 1)
        self.assertEqual(ImportJob.objects.count(), 1)
        job = ImportJob.objects.get()
        self.assertEqual((job.status, job.attempt), ('uploaded', 0))
        self.assertEqual((Path(self.temp.name) / job.archive_key).read_bytes(), self.zip_bytes())

    def test_concurrent_identical_bytes_are_private_per_owner(self):
        ids = self.race(['C5A', 'C5B', 'C5A', 'C5B'])
        self.assertEqual(ids[0], ids[2])
        self.assertEqual(ids[1], ids[3])
        self.assertNotEqual(ids[0], ids[1])
        self.assertEqual(ImportJob.objects.count(), 2)
        from cpjudge.imports import owned
        from django.http import Http404
        with self.assertRaises(Http404):
            owned(self.users['C5B'], ids[0])
        with self.assertRaises(Http404):
            owned(self.users['C5A'], ids[1])

    def test_same_owner_other_contest_rejection_cleans_duplicate(self):
        from cpjudge.policy import grant_scope
        owner = self.users['C5A']
        grant_scope(self.admin, owner, self.contests['c5b'], 'problems.import')
        original = upload(owner, SimpleUploadedFile('one.zip', self.zip_bytes()), self.contests['c5a'])
        before = list(ImportJob.objects.values())
        with self.assertRaises(ValidationError):
            upload(owner, SimpleUploadedFile('two.zip', self.zip_bytes()), self.contests['c5b'])
        self.assertEqual(list(ImportJob.objects.values()), before)
        self.assertEqual(list(Path(self.temp.name).glob('*.zip')),
                         [Path(self.temp.name) / original.archive_key])
