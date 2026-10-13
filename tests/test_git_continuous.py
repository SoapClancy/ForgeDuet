"""Long outages keep retrying without a model; all remotes/OS clients are fixtures."""
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import git_transport as gt
import handoff
import test_git_recovery as fixtures


class ContinuousTests(unittest.TestCase):
    def setUp(self):
        self.f=fixtures.RecoveryTests();self.f.setUp();self.addCleanup(self.f.doCleanups)
        self.build=self.f.build;self.review=self.f.review;self.remote=self.f.remote;self.offline=self.f.offline
        banner=patch.object(gt,'desktop_notice',return_value={'status':'sent'})
        self.banner=banner.start();self.addCleanup(banner.stop)

    def attempt(self, client=None):
        client=client or gt.GitTransport(self.build.config)
        retry=client.retry_state()
        with patch.object(gt.time,'time',return_value=(retry['next_retry_at'] or 1000)+1):
            return client.sync()

    def outage(self, count=7):
        self.remote.rename(self.offline)
        return [self.attempt() for _ in range(count)]

    def test_default_outage_beyond_threshold_keeps_retrying_without_model_input(self):
        results=self.outage(8)
        self.assertTrue(all(r['status']=='retrying' and r['model_calls']==0 for r in results))
        state=self.build.retry_state()
        self.assertEqual(state['consecutive_errors'],8);self.assertFalse(state['stopped'])
        self.assertEqual(state['next_retry_at']-state['last_error_at'],300)
        self.assertEqual(self.banner.call_count,1)
        for client in (self.build,self.review):
            self.assertEqual(list(client.root.glob('*/*.md')),[])
        self.assertEqual(len(list(self.build.runtime.glob('network-status-outage-*.json'))),1)

    def test_restart_preserves_deadline_then_recovers_and_delivers(self):
        self.f.f.report(self.build,'deliveries');self.outage()
        self.offline.rename(self.remote);rebuilt=gt.GitTransport(self.build.config)
        with patch.object(gt.time,'time',return_value=rebuilt.retry_state()['last_error_at']+1):
            with patch.object(rebuilt,'publish',side_effect=AssertionError('early network request')):
                self.assertEqual(rebuilt.sync()['status'],'retrying')
        result=self.attempt(rebuilt);self.assertEqual(result['network_status']['event'],'recovered')
        self.review.sync();self.assertTrue((self.review.root/'deliveries/round-1.md').exists())
        self.assertEqual(rebuilt.retry_state()['consecutive_errors'],0)
        self.assertEqual(self.banner.call_count,2)
        self.assertEqual(list(self.build.root.glob('reviews/*.md')),[])
        self.assertEqual([p.name for p in self.review.root.glob('deliveries/*.md')],['round-1.md'])
        rebuilt.sync();self.assertEqual(self.banner.call_count,2)

    def test_new_outage_gets_a_new_incident_and_one_notice_pair(self):
        for incident in (1,2):
            self.outage();self.offline.rename(self.remote);self.attempt()
            self.assertEqual(self.build.retry_state()['incident'],incident)
        self.assertEqual(self.banner.call_count,4)
        self.assertEqual(len(list(self.build.runtime.glob('network-status-*.json'))),4)

    def test_notification_failure_does_not_stop_retry_or_recovery(self):
        original=gt.atomic_json
        def fail_status(path,value):
            if path.name.startswith('network-status-'):raise OSError('synthetic full notification directory')
            return original(path,value)
        with patch.object(gt,'atomic_json',side_effect=fail_status):results=self.outage(6)
        self.assertIn('notification_error',results[-1]['network_status'])
        self.assertFalse(self.build.retry_state()['stopped']);self.assertEqual(self.banner.call_count,0)
        result=self.attempt();self.assertEqual(result['network_status']['event'],'outage')
        self.assertEqual(self.banner.call_count,1)
        self.offline.rename(self.remote)
        with patch.object(gt,'desktop_notice',side_effect=OSError('synthetic banner failure')):
            recovered=self.attempt()
        self.assertEqual(recovered['network_status']['desktop']['status'],'failed')
        self.assertEqual(self.build.retry_state()['consecutive_errors'],0)

    def test_recovery_receipt_prevents_duplicate_banner_after_crash_before_reset(self):
        self.outage();self.offline.rename(self.remote);original=gt.atomic_json
        def crash_reset(path,value):
            if path.name=='network-retry.json' and value['consecutive_errors']==0:
                raise OSError('synthetic crash before retry reset')
            return original(path,value)
        with patch.object(gt,'atomic_json',side_effect=crash_reset):
            with self.assertRaisesRegex(OSError,'synthetic crash'):self.attempt()
        self.assertEqual(self.banner.call_count,2)
        self.assertEqual(self.build.retry_state()['consecutive_errors'],7)
        self.attempt();self.assertEqual(self.banner.call_count,2)
        self.assertEqual(self.build.retry_state()['consecutive_errors'],0)

    def test_uncertain_os_attempt_is_not_replayed(self):
        self.remote.rename(self.offline)
        for _ in range(4):self.attempt()
        with patch.object(gt,'desktop_notice',side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):self.attempt()
        record=json.loads(next(self.build.runtime.glob('network-status-outage-*.json')).read_text())
        self.assertEqual(record['desktop']['status'],'pending')
        self.attempt();self.assertEqual(self.banner.call_count,0)

    def test_corrupt_informational_receipt_is_preserved_without_stopping(self):
        self.outage(5);path=next(self.build.runtime.glob('network-status-outage-*.json'))
        for corrupt in ('broken','[]','{"schema":1}'):
            path.write_text(corrupt);result=self.attempt()
            self.assertEqual(path.read_text(),corrupt);self.assertIn('notification_error',result['network_status'])
            self.assertFalse(self.build.retry_state()['stopped'])

    def test_retry_history_is_bounded_but_total_and_deadline_persist(self):
        self.build.sync()
        with patch.object(gt.GitTransport,'publish',side_effect=gt.RetryableGitError('synthetic network failure')):
            for _ in range(110):self.attempt()
        state=self.build.retry_state();self.assertEqual(state['consecutive_errors'],110)
        self.assertEqual(len(state['history']),100);self.assertEqual(self.banner.call_count,1)

    def test_common_https_failures_are_retryable(self):
        for message in ('OpenSSL SSL_connect: SSL_ERROR_SYSCALL', 'RPC failed; curl 56',
                        'unexpected disconnect while reading sideband packet',
                        'The requested URL returned error: 500', 'HTTP/2 429 Too Many Requests',
                        'HTTP 502', 'HTTP/1.1 503', 'HTTP 504'):
            with self.subTest(message=message):
                answer=subprocess.CompletedProcess([],128,b'',message.encode())
                with patch.object(gt.subprocess,'run',return_value=answer):
                    with self.assertRaises(gt.RetryableGitError):self.build.git('fetch',str(self.remote))

    def test_permanent_diagnostics_win_over_rpc_in_both_streams_without_truncation(self):
        for message in ('Authentication failed', 'HTTP/2 401', 'HTTP 403', 'HTTP 407',
                        'SSL certificate problem', 'curl 60 SSL peer certificate was not OK',
                        'curl 77 error setting certificate file', 'Host key verification failed', 'checksum mismatch',
                        '[remote rejected]', 'unpack failed', 'no space left on device'):
            for stream in ('stdout','stderr'):
                with self.subTest(message=message,stream=stream):
                    out=(b'x'*900+message.encode()) if stream=='stdout' else b''
                    err=b'RPC failed HTTP 500\n'+((b'x'*900+message.encode()) if stream=='stderr' else b'')
                    with patch.object(gt.subprocess,'run',return_value=subprocess.CompletedProcess([],128,out,err)):
                        with self.assertRaises(handoff.HandoffError) as caught:self.build.git('push',str(self.remote))
                    self.assertNotIsInstance(caught.exception,gt.RetryableGitError)

    def test_unknown_remote_and_local_plumbing_failures_still_stop(self):
        for op,message in (('fetch','unknown synthetic failure'),('hash-object','RPC failed HTTP 500')):
            with patch.object(gt.subprocess,'run',return_value=subprocess.CompletedProcess([],128,b'',message.encode())):
                with self.assertRaises(handoff.HandoffError) as caught:self.build.git(op,'fixture')
            self.assertNotIsInstance(caught.exception,gt.RetryableGitError)

    def test_legacy_identity_requires_explicit_reconciliation_without_overwrite(self):
        self.build.sync();path=self.build.journal;state=json.loads(path.read_text())
        state['identity'].pop('retry_policy');path.write_text(json.dumps(state));before=path.read_bytes()
        with self.assertRaisesRegex(handoff.HandoffError,'state'):gt.GitTransport(self.build.config).sync()
        self.assertEqual(path.read_bytes(),before)

    def test_invalid_policy_is_rejected_before_runtime_initialization(self):
        c=json.loads(self.build.config.read_text());c['network_failure_policy']='guess'
        self.build.config.write_text(json.dumps(c))
        with self.assertRaisesRegex(handoff.HandoffError,'policy'):gt.GitTransport(self.build.config)
        self.assertFalse(self.build.journal.exists())

    def test_real_watch_stays_alive_past_threshold_and_recovers(self):
        c=json.loads(self.build.config.read_text());c.update(interval=1,max_network_errors=2,retry_max_seconds=1,desktop_notifications=False)
        self.build.config.write_text(json.dumps(c));self.remote.rename(self.offline)
        self.f.f.report(self.build,'deliveries')
        process=subprocess.Popen([sys.executable,gt.__file__,'watch','--config',str(self.build.config)],
                                 stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True)
        def read():
            self.assertTrue(select.select([process.stdout],[],[],6)[0],'watch did not emit status')
            line=process.stdout.readline();self.assertTrue(line,'watch exited '+str(process.poll()))
            return json.loads(line)
        try:
            for count in (1,2,3):self.assertEqual(read()['consecutive_errors'],count)
            self.assertIsNone(process.poll())
            self.offline.rename(self.remote);self.assertIn('published',read());self.assertIsNone(process.poll())
        finally:
            if process.poll() is None:os.killpg(process.pid,signal.SIGTERM)
            process.wait(timeout=5);process.stdout.close();process.stderr.close()
        self.review.sync();self.assertEqual([p.name for p in self.review.root.glob('deliveries/*.md')],['round-1.md'])
        self.assertEqual(list(self.build.root.glob('reviews/*.md')),[])
