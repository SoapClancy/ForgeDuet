"""FD-BR-001 regressions: transport stop signals, with no real model or OS alerts."""
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

import test_markdown_bridge as base
import handoff
import markdown_bridge as mb


class BridgeStopNoticeTests(unittest.TestCase):
    def setUp(self):
        self.case = base.MarkdownBridgeTests()
        self.case.setUp()
        self.addCleanup(self.case.doCleanups)

    def notices(self):
        return list((self.case.root / 'reviews').glob('*-bridge-stopped-*.md'))

    def test_cli_failure_publishes_notice_that_build_watcher_can_detect_without_input_ack(self):
        c = self.case
        c.delivery()
        c.mode('fail')
        with self.assertRaises(handoff.HandoffError):
            c.bridge.watch(once=True)
        notices = self.notices()
        self.assertEqual(len(notices), 1)
        text = notices[0].read_text()
        self.assertIn('不是审查结论', text)
        self.assertIn('"review_verdict": null', text)
        self.assertIn('CLI failed', text)
        self.assertTrue(handoff.complete(notices[0].read_bytes()))
        self.assertIn(notices[0].name, (c.root / 'updates.log').read_text())
        build = handoff.Cursor(c.area / 'build.json')
        build.init(c.root, 'build')
        self.assertEqual(build.check(60)['events'][0]['path'], 'reviews/' + notices[0].name)
        self.assertEqual(c.cursor.load()['seen'], {})
        self.assertTrue(c.cursor.load()['paused'])
        self.assertEqual(len(c.calls()), 1)

    def test_unmarked_notice_is_deduplicated_without_ack_or_model_on_restart(self):
        c = self.case
        (c.root / 'deliveries/writing.md').write_text('Still incomplete')
        c.bridge.watch(once=True)
        now = handoff_time()
        with patch.object(handoff.time, 'time', return_value=now + 121):
            first = c.bridge.watch(once=True)
        with patch.object(handoff.time, 'time', return_value=now + 181):
            second = mb.Bridge(str(c.config)).watch(once=True)
        self.assertEqual(first['status'], 'attention')
        self.assertEqual(second['notification']['status'], 'deduplicated')
        self.assertEqual(len(self.notices()), 1)
        self.assertEqual(c.calls(), [])
        self.assertEqual(c.cursor.load()['seen'], {})
        self.assertEqual(c.cursor.load()['warning_seen'], {})

    def test_unresolved_restart_publishes_recovery_notice_without_dispatch(self):
        c = self.case
        c.delivery()
        c.bridge.save({'schema': 1, 'cursor': str(c.cursor.path), 'status': 'running', 'run_dir': 'retained fake run'})
        result = c.bridge.watch(once=True)
        self.assertEqual(result['status'], 'needs_recovery')
        self.assertEqual(len(self.notices()), 1)
        self.assertIn('needs_recovery', self.notices()[0].read_text())
        self.assertEqual(c.cursor.load()['seen'], {})
        self.assertEqual(c.calls(), [])

    def test_pre_dispatch_failure_identifies_new_input_without_reusing_previous_run(self):
        c = self.case
        c.delivery('one')
        c.bridge.watch(once=True)
        pending = c.delivery('two')
        c.settings['model'] = 'changed by config owner'
        c.write_config()
        with self.assertRaises(handoff.HandoffError):
            c.bridge.watch(once=True)
        receipt = json.loads((c.runtime / 'stop-notice.json').read_text())
        self.assertIsNone(receipt['detail']['run_dir'])
        self.assertEqual(receipt['detail']['events'][0]['path'], pending['path'])
        self.assertNotIn(pending['path'], c.cursor.load()['seen'])
        self.assertEqual(len(c.calls()), 1)

    def test_positive_timeout_is_mandatory_before_any_dispatch(self):
        c = self.case
        for timeout in (None, 0, -1, True, float('inf')):
            c.settings['timeout_seconds'] = timeout
            c.write_config()
            with self.subTest(timeout=timeout), self.assertRaises(handoff.HandoffError):
                mb.Bridge(str(c.config))
        self.assertEqual(c.calls(), [])

    def test_shared_lock_failure_uses_desktop_fallback_and_preserves_owner(self):
        c = self.case
        c.settings['desktop_notifications'] = True
        c.write_config()
        bridge = mb.Bridge(str(c.config))
        writer = handoff.Writer(c.root)
        token = writer.acquire('other writer', 'occupied')
        try:
            with patch.object(mb, 'desktop_notice', return_value={'status': 'submitted'}) as notify:
                result = bridge.notify_stop({'status': 'error', 'error': 'synthetic failure'})
            self.assertEqual(result['peer']['status'], 'failed')
            self.assertEqual(result['desktop']['status'], 'submitted')
            notify.assert_called_once()
            self.assertTrue((c.root / '.lock').exists())
            self.assertEqual(self.notices(), [])
            self.assertEqual(c.cursor.load()['seen'], {})
        finally:
            writer.release('other writer', token)
        # A later explicitly retried notification can publish without a second desktop alert.
        with patch.object(mb, 'desktop_notice') as notify:
            result = bridge.notify_stop({'status': 'error', 'error': 'synthetic failure'})
        self.assertEqual(result['peer']['status'], 'published')
        notify.assert_not_called()

    def test_desktop_failure_still_leaves_durable_peer_notice(self):
        c = self.case
        c.settings['desktop_notifications'] = True
        c.write_config()
        bridge = mb.Bridge(str(c.config))
        with patch.object(mb, 'desktop_notice', return_value={'status': 'failed', 'error': 'OS denied'}):
            result = bridge.notify_stop({'status': 'needs_recovery', 'run_dir': 'synthetic'})
        self.assertEqual(result['peer']['status'], 'published')
        self.assertEqual(result['desktop']['status'], 'failed')
        self.assertEqual(c.calls(), [])

    def test_corrupt_cursor_does_not_hide_primary_error_or_block_peer_notification(self):
        c = self.case
        c.delivery()
        def fail(*args):
            c.cursor.path.write_text('corrupt')
            raise handoff.HandoffError('PRIMARY injected failure')
        with patch.object(c.bridge, 'invoke', side_effect=fail):
            with self.assertRaisesRegex(handoff.HandoffError, 'PRIMARY injected failure'):
                c.bridge.watch(once=True)
        journal = json.loads(c.bridge.journal.read_text())
        self.assertEqual(journal['error'], 'PRIMARY injected failure')
        self.assertEqual(len(self.notices()), 1)
        self.assertIn('PRIMARY injected failure', self.notices()[0].read_text())

    def test_timeout_sends_transport_notice_and_retains_pending_input(self):
        c = self.case
        c.settings['timeout_seconds'] = 0.15
        c.write_config()
        bridge = mb.Bridge(str(c.config))
        c.delivery()
        c.mode('sleep')
        with self.assertRaisesRegex(handoff.HandoffError, 'timeout'):
            bridge.watch(once=True)
        self.assertIn('CLI timeout', self.notices()[0].read_text())
        self.assertEqual(c.cursor.load()['seen'], {})

    def test_scan_error_and_recovery_stops_publish_notices_without_a_model(self):
        c = self.case
        (c.root / 'deliveries/bad.md').write_bytes(b'\xff')
        c.bridge.watch(once=True)
        c.bridge.watch(once=True)
        result = c.bridge.watch(once=True)
        self.assertEqual(result['status'], 'error')
        self.assertEqual(len(self.notices()), 1)
        self.assertEqual(c.calls(), [])

    def test_dated_review_and_stop_notice_keep_review_ack_distinct(self):
        c = self.case
        item = c.delivery()
        c.mode('stop')
        result = c.bridge.watch(once=True)
        self.assertEqual(result['status'], 'paused')
        self.assertRegex(result['report']['path'], r'reviews/\d{4}-\d{2}-\d{2}-run-')
        self.assertEqual(len(self.notices()), 1)
        self.assertEqual(c.cursor.load()['seen'][item['path']], item['sha256'])
        self.assertIn('"input_acknowledged_by_notice": false', self.notices()[0].read_text())

    def test_notification_failure_does_not_replace_original_exception(self):
        c = self.case
        c.delivery()
        c.mode('fail')
        with patch.object(c.bridge, 'notify_stop', side_effect=OSError('SECONDARY notification failure')):
            with self.assertRaisesRegex(handoff.HandoffError, 'CLI failed'):
                c.bridge.watch(once=True)
        self.assertEqual(c.cursor.load()['seen'], {})

    def test_os_notification_uses_literal_arguments_and_a_bounded_local_process(self):
        attack = 'quote " and $(touch /nope)\nnewline'
        with patch.object(mb.sys, 'platform', 'darwin'), patch.object(mb.subprocess, 'run') as run:
            run.return_value.returncode = 0
            self.assertEqual(mb.desktop_notice(attack)['status'], 'submitted')
        argv = run.call_args.args[0]
        self.assertEqual(argv[0], '/usr/bin/osascript')
        self.assertEqual(argv[-1], attack)
        self.assertEqual(run.call_args.kwargs['timeout'], 5)
        self.assertNotIn('shell', run.call_args.kwargs)

    def test_os_notification_timeout_is_recorded_not_raised(self):
        with patch.object(mb.sys, 'platform', 'darwin'), patch.object(mb.subprocess, 'run', side_effect=subprocess.TimeoutExpired('osascript', 5)):
            self.assertEqual(mb.desktop_notice('synthetic')['status'], 'failed')


def handoff_time():
    return handoff.time.time()
