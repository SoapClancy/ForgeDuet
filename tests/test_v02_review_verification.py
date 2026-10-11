"""Additional edge checks for context-preserving control and CLI isolation."""
import json
from pathlib import Path
import subprocess
import sys
import unittest

import test_relay as base
import relay
sys.path.insert(0, str(base.ROOT / 'scripts/adapters'))
import common


class V02VerificationTests(unittest.TestCase):
    def setUp(self):
        self.case = base.RelayTests()
        self.case.setUp()
        self.addCleanup(self.case.doCleanups)

    def change_rules(self):
        c = self.case
        c.report('rules', '# New acceptance rule\n')
        fingerprint = c.box.status()['dispatch_hold']['observed_hash']
        c.box.adopt_rules(fingerprint, c.report('adoption'), 'Synthetic human adoption')

    def test_paused_adoption_does_not_publish_until_resume(self):
        c = self.case
        c.init()
        c.candidate()
        claim = c.box.claim('review', 'reviewer')
        c.finish(claim, c.result('needs_human', 'review'))
        before = c.box.status()['jobs']
        self.change_rules()
        state = c.box.status()
        self.assertEqual(state['phase'], 'needs_human')
        self.assertEqual(set(state['jobs']), set(before))
        self.assertIsNone(c.box.claim('review', 'not-resumed'))
        c.box.resume(c.report('resume'), 'review', 'Synthetic permission to continue')
        claim = c.box.claim('review', 'resumed')
        payload = json.loads(Path(claim['job_file']).read_text())
        self.assertEqual(payload['message']['report'], 'docs/forgeduet/candidate-build.md')
        self.assertEqual(len(payload['rules_history']), 1)
        self.assertEqual(payload['rules_history'][0]['report'], 'docs/forgeduet/adoption.md')

    def test_original_task_mutation_cannot_be_hidden_by_adoption(self):
        c = self.case
        c.init()
        c.task()
        c.report('task', '# Different task after publication\n')
        with self.assertRaisesRegex(relay.RelayError, 'Published report changed'):
            self.change_rules()
        self.assertTrue(c.box.status()['dispatch_hold'])

    def test_adoption_decision_remains_immutable(self):
        c = self.case
        c.init()
        c.task()
        self.change_rules()
        c.report('adoption', '# Rewritten human decision\n')
        with self.assertRaisesRegex(relay.RelayError, 'decision changed|adoption report changed'):
            c.box.claim('build', 'builder')

    def test_adoption_before_any_task_clears_hold_without_inventing_input(self):
        c = self.case
        c.init()
        self.change_rules()
        self.assertEqual(c.box.status()['jobs'], {})
        self.assertIsNone(c.box.claim('build', 'builder'))
        c.task()
        self.assertIsNotNone(c.box.claim('build', 'builder'))

    def test_multiple_adoptions_retain_task_and_decision_chain(self):
        c = self.case
        c.init()
        c.task()
        self.change_rules()
        c.report('rules', '# A third acceptance rule\n')
        fingerprint = c.box.status()['dispatch_hold']['observed_hash']
        c.box.adopt_rules(fingerprint, c.report('adoption-2'), 'Synthetic second decision')
        claim = c.box.claim('build', 'builder')
        payload = json.loads(Path(claim['job_file']).read_text())
        self.assertEqual(payload['message']['report'], 'docs/forgeduet/task.md')
        self.assertTrue(any(m.get('human_decision', {}).get('report') == 'docs/forgeduet/adoption.md'
                            for m in payload['context_messages']))
        self.assertEqual(len(payload['rules_history']), 2)
        self.assertNotIn('settings_verification', payload['message'])

    def test_human_redispatch_can_complete_a_fresh_review_and_acceptance(self):
        c = self.case
        c.init()
        c.candidate()
        review = c.box.claim('review', 'reviewer-1')
        c.finish(review, c.result('review_approved', 'review'))
        self.change_rules()
        review = c.box.claim('review', 'reviewer-2')
        c.finish(review, c.result('review_approved', 'review', name='new-approval'))
        build = c.box.claim('build', 'builder')
        c.finish(build, c.result('build_accepted', 'build'))
        self.assertEqual(c.box.status()['phase'], 'done')

    def test_verified_requires_recorded_verification_source(self):
        c = self.case
        c.cfg['roles']['build'].update(verification='verified', verification_source='')
        with self.assertRaisesRegex(relay.RelayError, 'verification_source'):
            c.init()
        c.cfg['roles']['build']['verification_source'] = 'Synthetic verifier observation'
        c.init()

    def prepare_cli(self, provider, role):
        c = self.case
        c.cfg['roles'][role].update(provider=provider, verification='self_reported')
        c.init()
        if role == 'review':
            c.candidate()
        else:
            c.task()
        claim = c.box.claim(role, 'synthetic-cli')
        cli = c.area / 'fake-cli'
        cli.write_text('#!' + sys.executable + '\n' + (base.ROOT / 'tests/fixture_cli.py').read_text())
        cli.chmod(0o755)
        output = c.area / 'result.json'
        argv = [sys.executable, str(base.ROOT / 'scripts/adapters' / (provider + '_adapter.py')), '--cli', str(cli)]
        if provider == 'codex':
            argv += ['--sandbox', 'workspace-write']
        return argv, [claim['job_file'], str(output)]

    def test_codex_review_launches_outside_candidate(self):
        c = self.case
        argv, tail = self.prepare_cli('codex', 'review')
        control = c.area / 'trusted-control'
        control.mkdir()
        (c.review / '.codex').mkdir()
        (c.review / '.codex/config.toml').write_text('# Synthetic candidate configuration\n')
        result = subprocess.run(argv + ['--control-dir', str(control)] + tail, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((c.review / 'cli-args.json').exists())
        flags = json.loads((control / 'cli-args.json').read_text())
        self.assertIn('project_doc_max_bytes=0', flags)
        self.assertIn('--skip-git-repo-check', flags)

    def test_codex_review_requires_disjoint_control_directory(self):
        c = self.case
        argv, tail = self.prepare_cli('codex', 'review')
        for extra in ([], ['--control-dir', str(c.review)], ['--control-dir', str(c.root / 'docs')],
                      ['--control-dir', str(c.area)]):
            result = subprocess.run(argv + extra + tail, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
        self.assertFalse((c.review / 'cli-args.json').exists())

    def test_review_cannot_load_skill_supplied_by_candidate(self):
        c = self.case
        argv, tail = self.prepare_cli('claude', 'review')
        payload = json.loads(Path(tail[0]).read_text())
        skill = c.review / 'SKILL.md'
        skill.write_text('# Candidate-supplied instructions, not authority')
        payload['settings']['skill_file'] = str(skill)
        Path(tail[0]).write_text(json.dumps(payload))
        result = subprocess.run(argv + tail, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((c.review / 'cli-args.json').exists())

    def test_write_dirs_cannot_exceed_recorded_grants(self):
        job = {'permissions': {'write_roots': [str(self.case.docs)]}}
        self.assertEqual(common.approved_write_dirs(job, [str(self.case.docs)]), [str(self.case.docs.resolve())])
        with self.assertRaisesRegex(ValueError, 'outside'):
            common.approved_write_dirs(job, [str(self.case.root)])

    def test_claude_allowed_tools_and_remaining_cost_are_explicit(self):
        c = self.case
        c.cfg['budgets']['usd'] = 0.9
        argv, tail = self.prepare_cli('claude', 'build')
        # This task has not spent anything yet; a prior run's spending would be carried in its setup.
        rules = 'Read,Edit(/synthetic/fixture/**),Bash(git status *)'
        result = subprocess.run(argv + ['--allowed-tools', rules] + tail, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        flags = json.loads((c.root / 'cli-args.json').read_text())
        self.assertEqual(flags[flags.index('--allowedTools') + 1], rules)
        self.assertEqual(flags[flags.index('--permission-prompts') + 1], 'none')
        self.assertAlmostEqual(float(flags[flags.index('--max-budget-usd') + 1]), 0.9)
        job = {'budgets': {'usd': 1.0}, 'remaining_context': {'usage': {'usd': 0.4}}}
        self.assertAlmostEqual(common.usd_remaining(job), 0.6)
        job['remaining_context']['usage']['usd'] = 1.0
        with self.assertRaisesRegex(ValueError, 'No USD budget'):
            common.usd_remaining(job)

    def test_extra_models_do_not_silently_pass_as_selected_model(self):
        raw = self.case.area / 'raw.json'
        raw.write_text(json.dumps({'structured_output': {}, 'modelUsage': {'selected': {}, 'extra': {}}}))
        with self.assertRaisesRegex(ValueError, 'model metadata'):
            common.claude_output(raw, 'selected')


if __name__ == '__main__':
    unittest.main()
