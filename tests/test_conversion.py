import tempfile
import unittest
import zipfile
from pathlib import Path

import yaml
from compat.convert import convert, Unsupported, extract
from tools.make_fixtures import build


class ConversionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        build(self.root / 'fixtures')

    def test_three_fixtures_preserve_data_limits_checker_and_groups(self):
        for name in ['tokens', 'multiple', 'groups']:
            with self.subTest(name=name):
                package = self.root / f'fixtures/{name}.zip'
                target = self.root / name
                convert(package, target)
                installed = target / name
                conf = yaml.safe_load((installed / 'init.yml').read_text())
                self.assertEqual(conf['time_limit'], .5)
                self.assertEqual(conf['memory_limit'], 65536)
                self.assertEqual(conf['checker']['args']['type'], 'testlib')
                self.assertEqual(conf['checker']['args']['lang'], 'CPP17')
                with zipfile.ZipFile(package) as src, zipfile.ZipFile(installed / 'data.zip') as dst:
                    for i in range(1, 4):
                        self.assertEqual(src.read(f'tests/{i:02}'), dst.read(f'{i}.in'))
                        self.assertEqual(src.read(f'tests/{i:02}.a'), dst.read(f'{i}.out'))
                    self.assertEqual(src.read('tests/01'), (installed / 'sidecar/samples/1.in').read_bytes())
                    for item in ['files/checker.cpp', 'files/testlib.h']:
                        self.assertEqual(src.read(item), (installed / Path(item).name).read_bytes())
                    self.assertEqual(src.read('statements/english/problem.html'), (installed / 'attachments/statements/english/problem.html').read_bytes())
                if name == 'groups':
                    self.assertEqual([c['points'] for c in conf['test_cases']], [30,50,20])
                    self.assertEqual(conf['test_cases'][1]['dependencies'], [1])
                else:
                    self.assertEqual(len(conf['test_cases']), 3)  # includes sample

    def mutate(self, transform):
        src = self.root / 'fixtures/groups.zip'
        dst = self.root / 'mutated.zip'
        with zipfile.ZipFile(src) as z, zipfile.ZipFile(dst, 'w') as out:
            for n in z.namelist():
                data = z.read(n)
                if n == 'problem.xml':
                    data = transform(data.decode()).encode()
                out.writestr(n, data)
        return dst

    def test_rejects_lossy_features(self):
        mutations = [
            lambda s: s.replace('complete-group', 'each-test'),
            lambda s: s.replace('points="30"', 'points="0"'),
            lambda s: s.replace('points="30"', 'points="3.5"'),
            lambda s: s.replace('<testset name="tests">', '<testset name="tests" points-policy="each-test">'),
            lambda s: s.replace('input-file=""', 'input-file="input.txt"'),
            lambda s: s.replace('type="testlib"', 'type="unknown"'),
            lambda s: s.replace('<checker ', '<interactor/><checker '),
            lambda s: s.replace('<test-count>3', '<test-count>4'),
            lambda s: s.replace('group="easy"/>', 'group="hard"/>'),  # forward/self dependency
            lambda s: s.replace('sample="true"', 'sample="true" points="7"'),
            lambda s: s.replace('files/checker.cpp', '../secret.cpp'),
            lambda s: s.replace('<time-limit>', '<unknown/><time-limit>'),
        ]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                with self.assertRaises(ValueError):
                    convert(self.mutate(mutation), self.root / 'rejected')
                self.assertFalse((self.root / 'rejected').exists())

    def test_rejects_traversal_duplicate_symlink_and_entity(self):
        for name, attrs in [('../escape', 0), ('link', 0o120777 << 16)]:
            with self.subTest(name=name):
                archive = self.root / 'unsafe.zip'
                with zipfile.ZipFile(archive, 'w') as z:
                    info = zipfile.ZipInfo(name)
                    info.external_attr = attrs
                    z.writestr(info, 'x')
                with self.assertRaises(Unsupported):
                    extract(archive, self.root / 'extract')
        p = self.mutate(lambda s: s.replace('<?xml version="1.0"?>', '<!DOCTYPE problem [<!ENTITY x SYSTEM "file:///etc/passwd">]>').replace('SYNTHETIC:', '&x;'))
        with self.assertRaises(Exception):
            convert(p, self.root / 'entity')

    def test_missing_answer_and_duplicate_zip_member(self):
        package = self.root / 'bad.zip'
        original = self.root / 'fixtures/tokens.zip'
        with zipfile.ZipFile(original) as src, zipfile.ZipFile(package, 'w') as dst:
            for n in src.namelist():
                if n != 'tests/03.a':
                    dst.writestr(n, src.read(n))
        with self.assertRaises(Unsupported):
            convert(package, self.root / 'missing')
        with zipfile.ZipFile(package, 'w') as z:
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
                z.writestr('same', '1')
                z.writestr('same', '2')
        with self.assertRaises(Unsupported):
            extract(package, self.root / 'duplicate')

    def test_limit_rounding_and_fixture_reproducibility(self):
        second = self.root / 'fixtures-again'
        build(second)
        for name in ['tokens', 'multiple', 'groups']:
            self.assertEqual((second / f'{name}.zip').read_bytes(), (self.root / f'fixtures/{name}.zip').read_bytes())
        package = self.mutate(lambda s: s.replace('67108864', '67108865'))
        convert(package, self.root / 'rounded')
        config = yaml.safe_load((self.root / 'rounded/groups/init.yml').read_text())
        self.assertEqual(config['memory_limit'], 65537)

    def test_refuses_existing_output(self):
        with self.assertRaises(Unsupported):
            convert(self.root / 'fixtures/tokens.zip', self.root)


if __name__ == '__main__':
    unittest.main()
