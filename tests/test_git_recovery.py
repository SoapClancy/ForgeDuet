"""FD-GIT-001/002 regressions. Real local Git remote; no clients/models."""
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import time
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import git_transport as gt
import handoff
import test_git_transport as fixtures


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.f=fixtures.GitTests();self.f.setUp();self.addCleanup(self.f.doCleanups)
        self.build=self.f.build;self.review=self.f.review;self.remote=self.f.remote
        self.offline=self.remote.with_name('remote-offline.git')

    def test_once_offline_defers_without_stop_notice(self):
        self.f.report(self.build,'deliveries');self.remote.rename(self.offline)
        result=self.build.sync()
        self.assertEqual(result['status'],'retrying')
        self.assertEqual(result['consecutive_errors'],1)
        self.assertEqual(list((self.build.root/'reviews').glob('git-transport-*.md')),[])

    def test_restart_honors_backoff_then_recovers_without_a_model(self):
        self.f.report(self.build,'deliveries');self.remote.rename(self.offline)
        first=self.build.sync();self.assertEqual(first['status'],'retrying')
        self.offline.rename(self.remote)
        rebuilt=gt.GitTransport(self.build.config)
        original=rebuilt.git
        def no_network(*args,**kwargs):
            self.assertNotIn(args[0],('ls-remote','fetch','push'))
            return original(*args,**kwargs)
        with patch.object(rebuilt,'git',side_effect=no_network):self.assertEqual(rebuilt.sync()['status'],'retrying')
        with patch.object(gt.time,'time',return_value=first['next_retry_at']+1):result=rebuilt.sync()
        self.assertEqual(result['model_calls'],0)
        self.review.sync()
        self.assertTrue((self.review.root/'deliveries/round-1.md').exists())
        self.assertEqual(json.loads((rebuilt.runtime/'network-retry.json').read_text())['consecutive_errors'],0)

    def test_watch_survives_a_real_remote_outage_and_recovers(self):
        c=json.loads(self.build.config.read_text());c.update(interval=1,desktop_notifications=False)
        self.build.config.write_text(json.dumps(c));self.remote.rename(self.offline)
        self.f.report(self.build,'deliveries')
        script=Path(gt.__file__)
        process=subprocess.Popen([sys.executable,str(script),'watch','--config',str(self.build.config)],
                                 stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True)
        try:
            self.assertTrue(select.select([process.stdout],[],[],5)[0],'no first status')
            line=process.stdout.readline();self.assertTrue(line,process.stderr.read() if process.poll() is not None else 'empty output')
            first=json.loads(line);self.assertEqual(first['status'],'retrying')
            self.assertIsNone(process.poll())
            self.offline.rename(self.remote)
            self.assertTrue(select.select([process.stdout],[],[],5)[0],'watch did not retry')
            result=json.loads(process.stdout.readline());self.assertIn('published',result)
            self.assertIsNone(process.poll())
        finally:
            if process.poll() is None:os.killpg(process.pid,signal.SIGTERM)
            process.wait(timeout=5);process.stdout.close();process.stderr.close()
        self.review.sync();self.assertTrue((self.review.root/'deliveries/round-1.md').exists())

    def test_network_retry_limit_survives_restart(self):
        self.remote.rename(self.offline);last=None
        for number in range(1,5):
            if last:
                with patch.object(gt.time,'time',return_value=last['next_retry_at']+1):last=gt.GitTransport(self.build.config).sync()
            else:last=self.build.sync()
            self.assertEqual(last['consecutive_errors'],number)
        with patch.object(gt.time,'time',return_value=last['next_retry_at']+1):
            with self.assertRaisesRegex(handoff.HandoffError,'Consecutive network failures'):gt.GitTransport(self.build.config).sync()
        with self.assertRaisesRegex(handoff.HandoffError,'resume'):gt.GitTransport(self.build.config).sync()

    def test_integrity_failure_is_immediate(self):
        self.f.report(self.build,'deliveries');self.build.sync()
        (self.build.root/'deliveries/round-1.md').write_text('changed\n交付完成\n')
        with self.assertRaisesRegex(handoff.HandoffError,'removed/changed'):self.build.sync()

    def test_builder_notice_is_local_input_only_and_not_exported(self):
        self.f.report(self.build,'deliveries')
        cursor=handoff.Cursor(self.build.runtime/'build-cursor.json');cursor.init(self.build.root,'build')
        with patch.object(gt,'desktop_notice',return_value={'status':'sent'}):self.build.notify('synthetic stop')
        events=cursor.check(60)['events'];self.assertEqual(len(events),1)
        self.assertTrue(events[0]['path'].startswith('reviews/git-transport-'))
        self.build.sync();self.review.sync()
        reviewer=handoff.Cursor(self.review.runtime/'review-cursor.json');reviewer.init(self.review.root,'review')
        self.assertEqual([e['path'] for e in reviewer.check(60)['events']],['deliveries/round-1.md'])

    def test_reviewer_notice_is_local_input_only_and_not_exported(self):
        self.f.report(self.review,'reviews')
        cursor=handoff.Cursor(self.review.runtime/'review-cursor.json');cursor.init(self.review.root,'review')
        with patch.object(gt,'desktop_notice',return_value={'status':'sent'}):self.review.notify('synthetic stop')
        events=cursor.check(60)['events'];self.assertEqual(len(events),1)
        self.assertTrue(events[0]['path'].startswith('deliveries/git-transport-'))
        self.review.sync();self.build.sync()
        self.assertEqual([p.name for p in (self.build.root/'reviews').glob('*.md')],['round-1.md'])

    def test_failed_local_publication_can_retry_without_repeating_banner(self):
        writer=handoff.Writer(self.build.root);token=writer.acquire('peer','synthetic lock holder')
        try:
            with patch.object(gt,'desktop_notice',return_value={'status':'sent'}) as banner:
                first=self.build.notify('same error');self.assertIn('local_error',first)
                writer.release('peer',token);token=None
                second=self.build.notify('same error');self.assertIn('local',second)
                third=self.build.notify('same error');self.assertEqual(second,third)
                self.assertEqual(banner.call_count,1)
        finally:
            if token:writer.release('peer',token)
        self.assertEqual(len(list((self.build.root/'reviews').glob('git-transport-*.md'))),1)

    def test_legacy_outbound_notice_and_local_response_never_exported(self):
        self.f.report(self.build,'deliveries','git-transport-'+'a'*64+'.md',text='record_type: transport_notice\nreview_verdict: null\nLegacy local stop')
        self.f.report(self.review,'reviews','git-transport-response-'+'b'*64+'.md',text='record_type: transport_notice_response\ntransport_scope: local')
        self.build.sync();self.review.sync();self.build.sync()
        self.assertEqual(list((self.review.root/'deliveries').glob('*.md')),[])
        self.assertEqual(list((self.build.root/'reviews').glob('*.md')),[])

    def test_reserved_notice_in_remote_snapshot_is_rejected(self):
        self.build.sync()
        name='deliveries/git-transport-'+'c'*64+'.md'
        data='record_type: transport_notice\n交付完成\n'.encode()
        manifest=dict(schema=1,run_id='fixture',role='build',files={name:gt.sha(data)})
        tree=self.build.tree({name:data,gt.MANIFEST:json.dumps(manifest).encode()})
        commit=self.build.git('commit-tree',tree,data=b'synthetic bad old client').decode().strip()
        self.build.git('push',str(self.remote),commit+':'+self.build.branch)
        with self.assertRaisesRegex(handoff.HandoffError,'Local-only'):self.review.sync()
        self.assertFalse((self.review.root/name).exists())

    def test_authentication_failure_is_not_retried(self):
        answer=subprocess.CompletedProcess([],128,b'',b'Permission denied (publickey).')
        with patch.object(gt.subprocess,'run',return_value=answer):
            with self.assertRaises(handoff.HandoffError) as caught:self.build.git('ls-remote',str(self.remote))
        self.assertNotIsInstance(caught.exception,gt.RetryableGitError)

    def test_only_remote_timeout_is_retryable(self):
        with patch.object(gt.subprocess,'run',side_effect=subprocess.TimeoutExpired('fixture',1)):
            with self.assertRaises(gt.RetryableGitError):self.build.git('fetch',str(self.remote))
            with self.assertRaises(subprocess.TimeoutExpired):self.build.git('hash-object','--stdin',data=b'x')

    def test_corrupt_retry_state_is_preserved(self):
        self.build.sync();path=self.build.runtime/'network-retry.json';path.write_text('broken')
        with self.assertRaises(ValueError):self.build.sync()
        self.assertEqual(path.read_text(),'broken')

    def test_once_cli_reports_retry_without_stopping_notice(self):
        c=json.loads(self.build.config.read_text());c['desktop_notifications']=False;self.build.config.write_text(json.dumps(c))
        self.remote.rename(self.offline)
        p=subprocess.run([sys.executable,gt.__file__,'once','--config',str(self.build.config)],text=True,capture_output=True,timeout=5)
        self.assertEqual(p.returncode,0,p.stderr);self.assertEqual(json.loads(p.stdout)['status'],'retrying')
        self.assertEqual(list((self.build.root/'reviews').glob('git-transport-*.md')),[])

    def test_exhausted_watch_stops_notifies_once_and_requires_resume(self):
        c=json.loads(self.build.config.read_text());c.update(interval=1,max_network_errors=2,retry_max_seconds=1,desktop_notifications=False)
        self.build.config.write_text(json.dumps(c));self.remote.rename(self.offline)
        command=[sys.executable,gt.__file__,'watch','--config',str(self.build.config)]
        first=subprocess.run(command,text=True,capture_output=True,timeout=5)
        self.assertEqual(first.returncode,2,first.stderr)
        notes=list((self.build.root/'reviews').glob('git-transport-*.md'));self.assertEqual(len(notes),1)
        second=subprocess.run(command,text=True,capture_output=True,timeout=5)
        self.assertEqual(second.returncode,2);self.assertEqual(len(list((self.build.root/'reviews').glob('git-transport-*.md'))),1)
        self.offline.rename(self.remote)
        resumed=subprocess.run([sys.executable,gt.__file__,'resume','--config',str(self.build.config)],text=True,capture_output=True,timeout=5)
        self.assertEqual(resumed.returncode,0,resumed.stderr)
        self.assertIn('published',gt.GitTransport(self.build.config).sync())

    def test_local_queue_notice_response_is_bound_acked_and_never_exported(self):
        import test_queue_bridge as queue_fixtures
        q=queue_fixtures.QueueTests();q.setUp();self.addCleanup(q.doCleanups)
        runtime=q.area/'git-runtime';runtime.mkdir()
        config=q.area/'git-config.json'
        config.write_text(json.dumps(dict(schema=1,role='review',run_id='fixture',remote=str(self.remote),
                                         mailbox=str(q.root),runtime=str(runtime),author='Fixture',email='fixture@example.invalid',desktop_notifications=False)))
        local=gt.GitTransport(config);local.notify('local transport needs human repair')
        submitted=q.bridge.watch(once=True);self.assertEqual(submitted['status'],'submitted')
        attempt=q.active();event=attempt['event'];self.assertTrue(event['path'].startswith('deliveries/git-transport-'))
        name='git-transport-response-'+attempt['key']+'.md'
        w=handoff.Writer(q.root);token=w.acquire('review','local transport handling only')
        try:
            w.publish('review',token,'reviews/'+name,'record_type: transport_notice_response\ntransport_scope: local\nQueue-Event-ID: '+attempt['key']+'\nInput-Path: '+event['path']+'\nInput-SHA256: '+event['sha256']+'\n\nLocal gate recorded; no source review or approval.')
        finally:w.release('review',token)
        q.cursor.ack(event['path'],event['sha256'])
        self.assertEqual(q.bridge.watch(once=True)['status'],'handled')
        self.assertEqual(len(q.calls()),1)
        local.sync();self.build.sync()
        self.assertEqual(list((self.build.root/'reviews').glob('*.md')),[])
