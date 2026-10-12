"""Bridge contracts using local synthetic CLI processes only; no real model calls."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import handoff
import markdown_bridge as mb


class MarkdownBridgeTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='fd-bridge-fake-')
        self.addCleanup(temp.cleanup)
        self.area = Path(temp.name).resolve()
        self.project = self.area / 'project'
        self.project.mkdir()
        self.root = self.project / 'handoff'
        self.root.mkdir()
        for name in ('deliveries', 'reviews'):
            (self.root / name).mkdir()
        self.control = self.area / 'control'
        self.control.mkdir()
        self.runtime = self.area / 'private-runtime'
        self.runtime.mkdir()
        self.instructions = self.area / 'trusted-instructions.md'
        self.instructions.write_text('Synthetic reviewer rules; no provider calls.')
        self.state = self.root / 'CURRENT.md'
        self.state.write_text('Synthetic task only. No project history or answer key.')
        self.cursor = handoff.Cursor(self.area / 'cursor.json')
        self.cursor.init(self.root, 'review')
        self.config = self.area / 'config.json'
        self.settings = dict(schema=1, cli=str(ROOT / 'tests/fixture_codex.py'),
                             model='fake-selected-model', effort='fake-selected-effort', owner='fake reviewer',
                             project_dir=str(self.project), control_dir=str(self.control),
                             runtime_dir=str(self.runtime), cursor=str(self.cursor.path),
                             instructions=str(self.instructions), state_file=str(self.state),
                             interval=0.05, timeout_seconds=10, desktop_notifications=False)
        self.write_config()
        self.bridge = mb.Bridge(str(self.config))

    def write_config(self):
        self.config.write_text(json.dumps(self.settings))

    def mode(self, value):
        (self.control / 'mode').write_text(value)

    def delivery(self, name='one'):
        writer = handoff.Writer(self.root)
        token = writer.acquire('fake builder', 'synthetic input')
        try:
            return writer.publish('fake builder', token, 'deliveries/' + name + '.md', '# Fake completed delivery')
        finally:
            writer.release('fake builder', token)

    def calls(self):
        path = self.control / 'calls.jsonl'
        return [json.loads(s) for s in path.read_text().splitlines()] if path.exists() else []

    def test_idle_repeated_checks_never_spawn_a_cli(self):
        with patch.object(mb.subprocess, 'Popen', side_effect=AssertionError('Idle must not spawn')):
            for _ in range(5):
                self.assertEqual(self.bridge.watch(once=True)['status'], 'waiting')
        self.assertEqual(self.calls(), [])
        self.assertFalse(self.bridge.journal.exists())

    def test_complete_dispatch_publish_log_then_ack_and_restart_dedup(self):
        item = self.delivery()
        original_ack = self.cursor.ack
        def ack(path, sha):
            self.assertFalse((self.root / '.lock').exists())
            reports = list((self.root / 'reviews').glob('*-run-*.md'))
            self.assertEqual(len(reports), 1)
            self.assertTrue(handoff.complete(reports[0].read_bytes()))
            self.assertIn('reviews/', (self.root / 'updates.log').read_text())
            original_ack(path, sha)
        with patch.object(self.bridge.cursor, 'ack', side_effect=ack):
            result = self.bridge.watch(once=True)
        self.assertEqual(result['status'], 'handled')
        self.assertEqual(self.cursor.load()['seen'][item['path']], item['sha256'])
        self.assertEqual(result['usage']['input_tokens'], 10)
        self.assertEqual(result['usage']['cached_input_tokens'], 2)
        self.assertEqual(result['usage']['cost'], 'unknown')
        self.assertEqual(mb.Bridge(str(self.config)).watch(once=True)['status'], 'waiting')
        self.assertEqual(len(self.calls()), 1)
        argv = self.calls()[0]['args']
        for flag in ('--ephemeral', '--json', '--output-schema', '--sandbox'):
            self.assertIn(flag, argv)
        self.assertEqual(argv[argv.index('--model') + 1], 'fake-selected-model')
        self.assertNotIn('--dangerously-bypass-approvals-and-sandbox', argv)
        self.assertEqual(self.calls()[0]['context']['event']['sha256'], item['sha256'])
        self.assertIsNone(self.cursor.load()['watcher'])

    def test_next_delivery_dispatches_and_mutated_record_is_explicit(self):
        self.delivery()
        self.bridge.watch(once=True)
        self.delivery('two')
        self.bridge.watch(once=True)
        one = self.root / 'deliveries/one.md'
        one.write_text(one.read_text() + '\ncorrected\n交付完成。\n')
        self.bridge.watch(once=True)
        self.assertEqual(len(self.calls()), 3)
        self.assertEqual(self.calls()[-1]['context']['event']['kind'], 'mutated_record')

    def test_unmarked_warning_does_not_invoke_or_ack(self):
        (self.root / 'deliveries/incomplete.md').write_text('# Still writing')
        self.bridge.watch(once=True)
        with patch.object(handoff.time, 'time', return_value=time.time() + 121):
            result = self.bridge.watch(once=True)
        self.assertEqual(result['status'], 'attention')
        self.assertEqual(self.calls(), [])
        self.assertEqual(self.cursor.load()['seen'], {})
        self.assertEqual(self.cursor.load()['warning_seen'], {})

    def test_failures_pause_keep_pending_and_never_auto_retry(self):
        for mode in ('fail', 'wrong', 'empty', 'no_answer', 'turn_failed', 'bad_jsonl', 'mutate', 'state_change'):
            with self.subTest(mode=mode):
                # Fresh independent mailbox per failure mode.
                other = MarkdownBridgeTests()
                other.setUp()
                try:
                    other.delivery()
                    other.mode(mode)
                    with self.assertRaises((handoff.HandoffError, OSError, ValueError)):
                        other.bridge.watch(once=True)
                    self.assertTrue(other.cursor.load()['paused'])
                    self.assertEqual(other.cursor.load()['seen'], {})
                    self.assertEqual(other.bridge.watch(once=True)['status'], 'needs_recovery')
                    self.assertEqual(len(other.calls()), 1)
                finally:
                    other.doCleanups()

    def test_recovery_is_explicit_and_does_not_ack_or_resume(self):
        self.delivery()
        self.mode('fail')
        with self.assertRaises(handoff.HandoffError):
            self.bridge.watch(once=True)
        recovered = self.bridge.recover('Human inspected logs; fake child ended; safe to retry')
        self.assertFalse(recovered['acknowledged_by_recovery'])
        self.assertEqual(self.cursor.load()['seen'], {})
        self.assertEqual(self.bridge.watch(once=True)['status'], 'paused')
        self.mode('ok')
        self.cursor.control(False, 'Human authorized retry after reconciliation')
        self.assertEqual(self.bridge.watch(once=True)['status'], 'handled')
        self.assertEqual(len(self.calls()), 2)

    def test_missing_usage_is_explicit_unknown_not_failed_transport(self):
        self.delivery()
        self.mode('no_usage')
        result = self.bridge.watch(once=True)
        self.assertEqual(result['status'], 'handled')
        self.assertEqual(result['usage']['status'], 'unknown')
        self.assertNotIn('input_tokens', result['usage'])

    def test_timeout_stops_own_child_and_pauses(self):
        self.settings['timeout_seconds'] = 0.15
        self.write_config()
        self.bridge = mb.Bridge(str(self.config))
        self.delivery()
        self.mode('sleep')
        with self.assertRaisesRegex(handoff.HandoffError, 'timeout'):
            self.bridge.watch(once=True)
        self.assertTrue(self.cursor.load()['paused'])
        self.assertEqual(self.cursor.load()['seen'], {})

    def test_stop_result_acknowledges_then_preserves_pause(self):
        item = self.delivery()
        self.mode('stop')
        self.assertEqual(self.bridge.watch(once=True)['status'], 'paused')
        self.assertEqual(self.cursor.load()['seen'][item['path']], item['sha256'])
        self.assertTrue(self.cursor.load()['paused'])
        self.assertEqual(self.bridge.watch(once=True)['status'], 'paused')
        self.assertEqual(len(self.calls()), 1)

    def test_shared_lock_blocks_publication_and_does_not_get_broken(self):
        self.delivery()
        writer = handoff.Writer(self.root)
        token = writer.acquire('other writer', 'occupied')
        try:
            with self.assertRaises(handoff.HandoffError):
                self.bridge.watch(once=True)
            self.assertTrue((self.root / '.lock').exists())
            self.assertEqual(self.cursor.load()['seen'], {})
            self.assertEqual(list((self.root / 'reviews').glob('*-run-*.md')), [])
            attempt = json.loads(self.bridge.journal.read_text())
            self.assertTrue(attempt['result']['review_markdown'])
        finally:
            writer.release('other writer', token)

    def test_ack_crash_retains_published_report_and_requires_reconciliation(self):
        self.delivery()
        with patch.object(self.bridge.cursor, 'ack', side_effect=OSError('injected crash before ack')):
            with self.assertRaises(OSError):
                self.bridge.watch(once=True)
        self.assertEqual(len(list((self.root / 'reviews').glob('*-run-*.md'))), 1)
        self.assertEqual(self.cursor.load()['seen'], {})
        self.assertEqual(self.bridge.watch(once=True)['status'], 'needs_recovery')
        self.assertEqual(len(self.calls()), 1)
        self.assertIn('report', json.loads(self.bridge.journal.read_text()))

    def test_concurrent_bridge_and_ordinary_watcher_are_excluded(self):
        for suffix in ('.bridge', '.watcher'):
            with self.subTest(suffix=suffix), self.cursor.guard(suffix, nonblock=True):
                with self.assertRaises(handoff.HandoffError):
                    self.bridge.watch(once=True)
        self.assertEqual(self.calls(), [])

    def test_configuration_and_instruction_changes_block_dispatch(self):
        item = self.delivery()
        self.settings['model'] = 'silently-changed-model'
        self.write_config()
        with self.assertRaises(handoff.HandoffError):
            self.bridge.watch(once=True)
        self.assertEqual(self.calls(), [])
        self.assertEqual(self.cursor.load()['seen'], {})

    def test_path_authority_guards_and_symlinks(self):
        bad = dict(self.settings)
        cases = [('control_dir', str(self.project)), ('runtime_dir', str(self.control)),
                 ('instructions', str(self.state)), ('cursor', str(self.config))]
        for key, value in cases:
            with self.subTest(key=key):
                self.settings = {**bad, key: value}
                self.write_config()
                with self.assertRaises((handoff.HandoffError, KeyError)):
                    mb.Bridge(str(self.config))
        self.settings = bad
        self.write_config()
        link = self.area / 'linked-config.json'
        link.symlink_to(self.config)
        with self.assertRaises(handoff.HandoffError):
            mb.Bridge(str(link))

    def test_running_journal_after_abrupt_exit_never_invokes_again(self):
        self.delivery()
        self.bridge.save({'schema': 1, 'cursor': str(self.cursor.path), 'status': 'running', 'run_dir': 'synthetic'})
        self.assertEqual(self.bridge.watch(once=True)['status'], 'needs_recovery')
        self.assertEqual(self.calls(), [])

    def test_instruction_mutation_before_call_is_rejected(self):
        self.delivery()
        self.instructions.write_text('changed trusted instructions')
        with self.assertRaises(handoff.HandoffError):
            self.bridge.watch(once=True)
        self.assertEqual(self.calls(), [])

    def test_three_scan_failures_pause_without_cli_and_retain_diagnostics(self):
        (self.root / 'deliveries/broken.md').write_bytes(b'\xff')
        self.assertEqual(self.bridge.watch(once=True)['status'], 'retrying')
        self.assertEqual(self.bridge.watch(once=True)['status'], 'retrying')
        self.assertEqual(self.bridge.watch(once=True)['status'], 'error')
        self.assertTrue(self.cursor.load()['paused'])
        self.assertEqual(self.cursor.load()['scan_errors'], 3)
        self.assertEqual(self.calls(), [])

    def test_pause_during_child_stops_it_and_excludes_second_process(self):
        self.delivery()
        self.mode('sleep')
        proc = subprocess.Popen([sys.executable, str(ROOT / 'scripts/markdown_bridge.py'),
                                 'watch', '--config', str(self.config)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            until = time.monotonic() + 5
            while not (self.control / 'started').exists() and time.monotonic() < until:
                time.sleep(0.02)
            self.assertTrue((self.control / 'started').exists())
            self.assertFalse((self.root / '.lock').exists(), 'No shared lock during child work')
            with self.assertRaises(handoff.HandoffError):
                self.bridge.watch(once=True)
            self.cursor.control(True, 'Human pause during synthetic child')
            stdout, stderr = proc.communicate(timeout=5)
            self.assertEqual(proc.returncode, 2, stderr)
            self.assertIn('Paused during CLI work', stdout.decode())
            self.assertEqual(self.cursor.load()['seen'], {})
            self.assertEqual(len(self.calls()), 1)
        finally:
            if proc.poll() is None:
                proc.terminate()
                proc.wait(timeout=5)

    def test_publication_log_failure_retains_report_without_ack(self):
        self.delivery()
        original = handoff.Writer.log
        with patch.object(handoff.Writer, 'log', side_effect=OSError('injected log failure')):
            with self.assertRaises(OSError):
                self.bridge.watch(once=True)
        self.assertEqual(len(list((self.root / 'reviews').glob('*-run-*.md'))), 1)
        self.assertEqual(self.cursor.load()['seen'], {})
        self.assertFalse((self.root / '.lock').exists())
        self.assertEqual(self.bridge.watch(once=True)['status'], 'needs_recovery')
        self.assertEqual(len(self.calls()), 1)

    def test_usage_parser_rejects_ambiguous_negative_boolean_and_overlapping_counts(self):
        path = self.area / 'usage.jsonl'
        for value in ({'input_tokens': True, 'output_tokens': 1},
                      {'input_tokens': 1, 'output_tokens': -1},
                      {'input_tokens': 1, 'output_tokens': 2, 'cached_input_tokens': 3},
                      {'input_tokens': 1, 'output_tokens': 2, 'reasoning_output_tokens': 3}):
            path.write_text(json.dumps({'type': 'turn.completed', 'usage': value}))
            self.assertEqual(mb.usage(path)['status'], 'unknown')
        event = json.dumps({'type': 'turn.completed', 'usage': {'input_tokens': 1, 'output_tokens': 2}})
        path.write_text(event + '\n' + event)
        self.assertEqual(mb.usage(path)['status'], 'unknown')

    def test_real_local_loop_waits_then_dispatches_once(self):
        proc = subprocess.Popen([sys.executable, str(ROOT / 'scripts/markdown_bridge.py'),
                                 'watch', '--config', str(self.config)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            time.sleep(0.3)
            self.assertIsNone(proc.poll())
            self.assertEqual(self.calls(), [])
            self.mode('stop')
            self.delivery()
            stdout, stderr = proc.communicate(timeout=10)
            self.assertEqual(proc.returncode, 3, stderr)
            self.assertEqual(json.loads(stdout)['status'], 'paused')
            self.assertEqual(len(self.calls()), 1)
        finally:
            if proc.poll() is None:
                proc.terminate()
                proc.wait(timeout=5)


if __name__ == '__main__':
    unittest.main()
