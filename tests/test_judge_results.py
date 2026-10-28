import unittest
from tools.judge_results import summarize


class JudgeEvidenceTests(unittest.TestCase):
    def log(self, verdicts):
        return '\n'.join(['Testing problem gaming-grid...', 'Running test reference',
                          *[f'Test case {i} {code} [0.001s]' for i, code in enumerate(verdicts, 1)],
                          'Result of test reference: Success', 'All tests passed.'])

    def test_requires_every_case(self):
        expected = {'gaming-grid': {'reference': ['AC'] * 103}}
        self.assertEqual(summarize(self.log(['AC'] * 103), expected, 0)['status'], 'PASS')
        self.assertEqual(summarize(self.log(['AC'] * 102), expected, 0)['status'], 'FAIL')
        self.assertEqual(summarize('All tests passed.', expected, 0)['status'], 'FAIL')

    def test_separates_skips_checker_errors_and_compile_errors(self):
        expected = {'gaming-grid': {'reference': ['AC']}}
        for message, category in [('Skipped - Language not supported', 'SKIPPED_OR_MISSING_EXECUTOR'),
                                  ('Unexpected internal error: checker failed assertion', 'JUDGE_OR_CHECKER_ERROR'),
                                  ('Unexpected compile error', 'COMPILATION_ERROR')]:
            result = summarize(self.log(['AC']) + '\n' + message, expected, 0)
            self.assertEqual(result['status'], 'FAIL')
            self.assertIn(category, result['issues'])

    def test_dependency_skip_and_wrong_verdict(self):
        expected = {'gaming-grid': {'reference': ['WA', 'SC', 'AC']}}
        self.assertEqual(summarize(self.log(['WA', '--', 'AC']), expected, 0)['status'], 'PASS')
        self.assertEqual(summarize(self.log(['RTE', '--', 'AC']), expected, 0)['status'], 'FAIL')


class WrongAnswerProbeTests(unittest.TestCase):
    def test_real_probe_uses_valid_tokens_and_checks_semantic_verdicts(self):
        import tempfile
        import zipfile
        from pathlib import Path
        import yaml
        from tools.install_judge_tests import install
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            # Synthetic stand-in for gaming-grid probe setup; no judging occurs.
            reference = root / 'reference.cpp'
            reference.write_text('int main(){}')
            (root / 'init.yml').write_text(yaml.safe_dump({
                'archive': 'data.zip', 'time_limit': 2, 'memory_limit': 262144,
                'test_cases': [{'in': '1.in', 'out': '1.out'}, {'in': '2.in', 'out': '2.out'}]}))
            with zipfile.ZipFile(root / 'data.zip', 'w') as data:
                data.writestr('1.out', 'yes\n2 3\n')
                data.writestr('2.out', 'no\n')
            install(root, 'gaming-grid', reference)
            config = yaml.safe_load((root / 'init.yml').read_text())
            probe = next(t for t in config['tests'] if t['label'] == 'wrong_answer')
            self.assertEqual(probe['cases'], ['WA', 'AC'])
            self.assertEqual(probe['feedback'], '')
            source = (root / probe['source']).read_text()
            self.assertIn('"NO\\n"', source)
            self.assertNotIn('-999', source)
