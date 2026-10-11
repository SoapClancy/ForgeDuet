"""Independent reproductions derived from Claude's v0.2 review; disposable fixtures only."""
import json
from pathlib import Path
import subprocess
import sys
import unittest

import test_relay as base
import relay


class V02ReviewTests(unittest.TestCase):
    def setUp(self):
        self.case = base.RelayTests()
        self.case.setUp()
        self.addCleanup(self.case.doCleanups)

    def job(self, role):
        claim = self.case.box.claim(role, 'synthetic-role')
        self.assertIsNotNone(claim)
        return json.loads(Path(claim['job_file']).read_text())

    def adopt(self):
        c = self.case
        c.report('rules', '# Changed acceptance rules\n')
        decision = c.report('adoption', '# Human adopted rules; original task unchanged\n')
        fingerprint = c.box.status()['dispatch_hold']['observed_hash']
        c.box.adopt_rules(fingerprint, decision, 'Synthetic human adoption')
        return decision

    def assert_original_input(self, payload, report, decision):
        message = payload['message']
        self.assertEqual(message['report'], report)
        self.assertEqual(message['sender'], 'human')
        self.assertNotIn('settings_verification', message)
        self.assertIsNotNone(message['reply_to'])
        self.assertEqual(message['human_decision']['report'], decision)
        self.assertTrue(any(m['report'] == report for m in payload['context_messages']))
        self.assertTrue(any(m['report'] == 'docs/forgeduet/task.md' for m in payload['context_messages']))

    def test_adopt_before_build_preserves_original_task(self):
        c = self.case
        c.init()
        c.task()
        decision = self.adopt()
        self.assert_original_input(self.job('build'), 'docs/forgeduet/task.md', decision)

    def test_adopt_after_approval_preserves_build_delivery(self):
        c = self.case
        c.init()
        c.candidate()
        claim = c.box.claim('review', 'reviewer')
        c.finish(claim, c.result('review_approved', 'review'))
        decision = self.adopt()
        self.assert_original_input(self.job('review'), 'docs/forgeduet/candidate-build.md', decision)

    def test_resume_build_preserves_original_task_and_escalation(self):
        c = self.case
        c.init()
        c.task()
        claim = c.box.claim('build', 'builder')
        c.finish(claim, c.result('needs_human', 'build'))
        decision = c.report('resume', '# Human resolved the question\n')
        c.box.resume(decision, 'build', 'Synthetic continue')
        payload = self.job('build')
        self.assert_original_input(payload, 'docs/forgeduet/task.md', decision)
        self.assertTrue(any(m['kind'] == 'needs_human' for m in payload['context_messages']))

    def test_resume_review_preserves_candidate_and_task(self):
        c = self.case
        c.init()
        c.candidate()
        claim = c.box.claim('review', 'reviewer')
        c.finish(claim, c.result('needs_human', 'review'))
        decision = c.report('resume', '# Human supplied missing evidence\n')
        c.box.resume(decision, 'review', 'Synthetic continue')
        self.assert_original_input(self.job('review'), 'docs/forgeduet/candidate-build.md', decision)

    def test_claude_review_does_not_autorun_candidate_hook(self):
        c = self.case
        c.cfg['roles']['review'].update(provider='claude', verification='self_reported')
        c.init()
        c.candidate()
        claim = c.box.claim('review', 'synthetic-reviewer')
        marker = c.area / 'candidate-hook-ran'
        folder = c.review / '.claude'
        folder.mkdir()
        (folder / 'settings.json').write_text(json.dumps({'synthetic_hook_marker': str(marker)}))
        cli = c.area / 'fake-cli'
        cli.write_text('#!' + sys.executable + '\n' + (base.ROOT / 'tests/fixture_cli.py').read_text())
        cli.chmod(0o755)
        result = c.area / 'result.json'
        completed = subprocess.run([sys.executable, str(base.ROOT / 'scripts/adapters/claude_adapter.py'),
                                    '--cli', str(cli), claim['job_file'], str(result)],
                                   capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertFalse(marker.exists(), 'Synthetic client auto-ran candidate configuration')
        flags = json.loads((c.review / 'cli-args.json').read_text())
        self.assertIn('--safe-mode', flags)
        self.assertEqual(flags[flags.index('--setting-sources') + 1], 'user')


if __name__ == '__main__':
    unittest.main()
