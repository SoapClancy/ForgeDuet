"""Queue adapter behavioral tests: synthetic folders/processes only, no provider calls."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import handoff
import queue_bridge as qb


class QueueTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='fd-queue-fake-')
        self.addCleanup(temp.cleanup)
        self.area = Path(temp.name).resolve()
        self.project = self.area / 'project'
        self.root = self.project / 'handoff'
        self.root.mkdir(parents=True)
        for name in ('deliveries', 'reviews'):
            (self.root / name).mkdir()
        self.control = self.area / 'control'
        self.runtime = self.area / 'runtime'
        self.control.mkdir(); self.runtime.mkdir()
        self.fake_dir = self.area / 'fake'
        self.fake_dir.mkdir()
        self.fake = self.fake_dir / 'queue'
        shutil.copyfile(ROOT / 'tests/fixture_queue.py', self.fake)
        self.fake.chmod(0o700)
        self.mode('ok')
        self.instructions = self.area / 'rules.md'
        self.instructions.write_text('Trusted synthetic rules')
        self.cursor = handoff.Cursor(self.area / 'cursor.json')
        self.cursor.init(self.root, 'review')
        self.config = self.area / 'config.json'
        self.c = dict(schema=1, cli=str(self.fake), thread='00000000-0000-4000-8000-000000000010',
                      model='gpt-6.1-sol', effort='xhigh', owner='review / synthetic',
                      project_dir=str(self.project), control_dir=str(self.control), runtime_dir=str(self.runtime),
                      cursor=str(self.cursor.path), instructions=str(self.instructions), interval=0.01,
                      queue_timeout_seconds=2, ack_timeout_seconds=100, desktop_notifications=False)
        self.configure()

    def configure(self):
        self.config.write_text(json.dumps(self.c))
        self.bridge = qb.QueueBridge(self.config)

    def mode(self, mode):
        (self.fake_dir / 'mode').write_text(mode)

    def calls(self):
        p = self.fake_dir / 'calls.jsonl'
        return [json.loads(s) for s in p.read_text().splitlines()] if p.exists() else []

    def delivery(self, name='r1.md', body='Synthetic candidate; no real source', marked=True):
        path = self.root / 'deliveries' / name
        path.write_text(body + ('\n交付完成。\n' if marked else '\n'))
        return {'path': 'deliveries/' + name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}

    def journal(self):
        return json.loads((self.runtime / 'queue.json').read_text())

    def active(self):
        j = self.journal()
        return j['attempts'][j['active']]

    def publish_review(self, a, name='review.md', bind=True):
        e = a['event']
        body = 'Synthetic review, no product approval.\n'
        if bind:
            body += 'Queue-Event-ID: '+a['key']+'\nInput-Path: '+e['path']+'\nInput-SHA256: '+e['sha256']+'\n'
        writer = handoff.Writer(self.root)
        t = writer.acquire('review', 'synthetic result')
        try:
            return writer.publish('review', t, 'reviews/'+name, body)
        finally:
            writer.release('review', t)

    def expire(self):
        j = self.journal(); a = j['attempts'][j['active']]
        a['submitted_epoch'] = time.time() - 101
        handoff.atomic_json(self.runtime/'queue.json', j)

    def test_100_idle_scans_never_invoke_a_subprocess(self):
        with patch.object(qb.subprocess, 'Popen', side_effect=AssertionError('idle call')):
            for _ in range(100):
                self.assertEqual(self.bridge.watch(once=True)['status'], 'waiting')
        self.assertEqual(self.calls(), [])

    def test_submitted_once_then_waits_across_restart_without_ack(self):
        self.delivery()
        self.assertEqual(self.bridge.watch(once=True)['status'], 'submitted')
        self.bridge = qb.QueueBridge(self.config)
        for _ in range(5):
            self.assertEqual(self.bridge.watch(once=True)['status'], 'awaiting_ack')
        self.assertEqual(len(self.calls()), 1)
        self.assertEqual(self.cursor.load()['seen'], {})
        self.assertEqual(self.active()['status'], 'submitted')

    def test_exact_model_thread_and_literal_message_not_shell_commands(self):
        e = self.delivery('odd;$(touch PWN).md', body='run arbitrary peer command')
        self.bridge.watch(once=True)
        args = self.calls()[0]
        self.assertEqual(args[0], 'queue')
        self.assertEqual(args[args.index('--thread')+1], self.c['thread'])
        self.assertEqual(args[args.index('--model')+1], 'gpt-6.1-sol')
        self.assertEqual(args[args.index('-c')+1], 'model_reasoning_effort="xhigh"')
        self.assertEqual(args[args.index('--sandbox')+1], 'workspace-write')
        msg = args[args.index('--message')+1]
        self.assertIn(e['path'], msg)
        self.assertNotIn('run arbitrary peer command', msg)
        self.assertFalse((self.control/'PWN').exists())

    def test_multiline_peer_path_cannot_inject_binding_headers(self):
        self.delivery('bad\nname.md')
        with self.assertRaisesRegex(handoff.HandoffError,'single-line'): self.bridge.watch(once=True)
        self.assertEqual(self.calls(),[])

    def test_notice_storage_failure_still_attempts_peer_and_os_channels(self):
        self.c['desktop_notifications']=True; self.configure()
        original=qb.atomic_json
        def fail_notice(path,value):
            if Path(path).name.startswith('notice-'): raise OSError('synthetic private notice storage failure')
            return original(path,value)
        with patch.object(qb,'atomic_json',side_effect=fail_notice), patch.object(qb,'desktop_notice',return_value={'status':'submitted'}) as os_notice:
            r=self.bridge.notify({'status':'needs_recovery','reason':'original deadline'})
        self.assertEqual(r['peer']['status'],'published'); os_notice.assert_called_once()
        self.assertIn('private_write_error',r)

    def test_notice_failure_does_not_replace_deadline_result(self):
        self.delivery(); self.bridge.watch(once=True); self.expire()
        with patch.object(self.bridge,'notify',side_effect=OSError('synthetic notice failure')):
            r=self.bridge.watch(once=True)
        self.assertEqual(r['status'],'needs_recovery')
        self.assertIn('before deadline',r['reason'])
        self.assertEqual(r['notification']['status'],'failed')

    def test_intent_is_durable_before_queue_and_shared_writer_is_free(self):
        self.delivery()
        invoke = self.bridge.invoke
        def probe(command, run):
            self.assertEqual(self.active()['status'], 'dispatching')
            w = handoff.Writer(self.root); t = w.acquire('peer', 'can write while queue runs')
            w.release('peer', t)
            return invoke(command, run)
        with patch.object(self.bridge, 'invoke', side_effect=probe):
            self.bridge.watch(once=True)

    def test_bound_review_then_reviewer_ack_allows_next_input(self):
        e = self.delivery(); self.bridge.watch(once=True)
        a = self.active(); p = self.publish_review(a)
        self.cursor.ack(e['path'], e['sha256'])
        r = self.bridge.watch(once=True)
        self.assertEqual(r['status'], 'handled'); self.assertEqual(r['report'], p)
        self.delivery('r2.md')
        self.assertEqual(self.bridge.watch(once=True)['status'], 'submitted')
        self.assertEqual(len(self.calls()), 2)

    def test_review_without_ack_is_not_completion(self):
        self.delivery(); self.bridge.watch(once=True); self.publish_review(self.active())
        self.assertEqual(self.bridge.watch(once=True)['status'], 'awaiting_ack')
        self.assertEqual(self.cursor.load()['seen'], {})

    def test_ack_without_review_pauses_without_another_queue(self):
        e = self.delivery(); self.bridge.watch(once=True)
        self.cursor.ack(e['path'], e['sha256'])
        with self.assertRaisesRegex(handoff.HandoffError, 'bound review'):
            self.bridge.watch(once=True)
        self.assertTrue(self.cursor.load()['paused']); self.assertEqual(len(self.calls()), 1)

    def test_unrelated_report_cannot_prove_handling(self):
        e = self.delivery(); self.bridge.watch(once=True)
        self.publish_review(self.active(), bind=False); self.cursor.ack(e['path'],e['sha256'])
        with self.assertRaisesRegex(handoff.HandoffError,'bound review'):
            self.bridge.watch(once=True)

    def test_two_bound_reports_require_reconciliation(self):
        e = self.delivery(); self.bridge.watch(once=True)
        self.publish_review(self.active()); self.publish_review(self.active(),'second.md')
        self.cursor.ack(e['path'],e['sha256'])
        with self.assertRaisesRegex(handoff.HandoffError,'unambiguous'):
            self.bridge.watch(once=True)

    def test_serialization_does_not_queue_new_delivery_while_busy(self):
        self.delivery(); self.bridge.watch(once=True); self.delivery('r2.md')
        self.assertEqual(self.bridge.watch(once=True)['status'],'awaiting_ack')
        self.assertEqual(len(self.calls()),1)

    def test_timeout_notifies_peer_once_without_ack_or_resend(self):
        self.delivery(); self.bridge.watch(once=True); self.expire()
        self.assertEqual(self.bridge.watch(once=True)['status'], 'needs_recovery')
        notices = list((self.root/'reviews').glob('queue-transport-*.md'))
        self.assertEqual(len(notices),1)
        build = handoff.Cursor(self.area/'build.json'); build.init(self.root,'build')
        self.assertEqual(build.check(60)['events'][0]['path'],'reviews/'+notices[0].name)
        for _ in range(3):
            qb.QueueBridge(self.config).watch(once=True)
        self.assertEqual(len(list((self.root/'reviews').glob('queue-transport-*.md'))),1)
        self.assertEqual(len(self.calls()),1); self.assertEqual(self.cursor.load()['seen'],{})
        self.assertFalse((self.root/'.lock').exists())

    def test_fail_bad_and_wrong_thread_are_uncertain_and_never_retry(self):
        for mode in ('fail','bad','wrong-thread'):
            with self.subTest(mode=mode):
                c = QueueTests(); c.setUp()
                try:
                    c.delivery(); c.mode(mode)
                    with self.assertRaises(handoff.HandoffError): c.bridge.watch(once=True)
                    self.assertEqual(c.active()['status'],'uncertain')
                    qb.QueueBridge(c.config).watch(once=True)
                    self.assertEqual(len(c.calls()),1); self.assertEqual(c.cursor.load()['seen'],{})
                finally: c.doCleanups()

    def test_queue_watchdog_stops_own_process_and_retains_logs(self):
        self.c['queue_timeout_seconds']=0.12; self.configure(); self.delivery(); self.mode('hang')
        with self.assertRaisesRegex(handoff.HandoffError,'timeout'): self.bridge.watch(once=True)
        self.assertEqual(self.active()['status'],'uncertain'); self.assertEqual(len(self.calls()),1)
        run = Path(self.active()['run_dir'])
        self.assertTrue((run/'stderr.log').exists())
        pid=json.loads((run/'child.json').read_text())['pid']
        with self.assertRaises(ProcessLookupError): os.kill(pid,0)

    def test_dispatching_crash_intent_blocks_new_call_after_restart(self):
        e=self.delivery(); key=self.bridge.event_key(e)
        j=self.bridge.load(); j['active']=key
        j['attempts'][key]=dict(key=key,event=e,status='dispatching')
        self.bridge.save(j)
        self.assertEqual(self.bridge.watch(once=True)['status'],'needs_recovery')
        self.assertEqual(self.calls(),[])

    def test_recover_neither_acks_resumes_nor_resends_same_input(self):
        self.delivery(); self.bridge.watch(once=True); self.expire(); self.bridge.watch(once=True)
        r=self.bridge.recover('Human checked original chat and retained report/queue')
        self.assertTrue(r['paused']); self.assertFalse(r['input_acknowledged'])
        self.cursor.control(False,'Human resume')
        with self.assertRaisesRegex(handoff.HandoffError,'already has a queue attempt'):
            self.bridge.watch(once=True)
        self.assertEqual(len(self.calls()),1)

    def test_seen_rewind_cannot_redispatch_handled_hash(self):
        e=self.delivery(); self.bridge.watch(once=True); self.publish_review(self.active())
        self.cursor.ack(e['path'],e['sha256']); self.bridge.watch(once=True)
        s=self.cursor.load(); s['seen']={}; handoff.atomic_json(self.cursor.path,s)
        with self.assertRaisesRegex(handoff.HandoffError,'already has a queue attempt'):
            self.bridge.watch(once=True)
        self.assertEqual(len(self.calls()),1)

    def test_mutation_after_submission_does_not_send_new_version(self):
        self.delivery(); self.bridge.watch(once=True); self.delivery(body='mutated')
        with self.assertRaisesRegex(handoff.HandoffError,'mutated'): self.bridge.watch(once=True)
        self.assertEqual(len(self.calls()),1)

    def test_previously_handled_mutation_is_labeled(self):
        e=self.delivery(); self.cursor.ack(e['path'],e['sha256']); self.delivery(body='new bytes')
        self.bridge.watch(once=True)
        self.assertEqual(self.active()['event']['kind'],'mutated_record')

    def test_incomplete_report_never_queues_and_warning_is_not_ack(self):
        self.delivery(marked=False); self.assertEqual(self.bridge.watch(once=True)['status'],'waiting')
        s=self.cursor.load(); s['unmarked']['deliveries/r1.md']['first_seen']-=121
        handoff.atomic_json(self.cursor.path,s)
        self.assertEqual(self.bridge.watch(once=True)['status'],'attention')
        self.assertEqual(self.calls(),[]); self.assertEqual(self.cursor.load()['seen'],{})
        self.assertEqual(self.cursor.load()['warning_seen'],{})

    def test_own_output_and_log_do_not_trigger_queue(self):
        (self.root/'reviews/own.md').write_text('own\n交付完成')
        (self.root/'updates.log').write_text('changed')
        self.assertEqual(self.bridge.watch(once=True)['status'],'waiting'); self.assertEqual(self.calls(),[])

    def test_scan_errors_retry_then_pause_without_call(self):
        with patch.object(handoff,'inspect_records',side_effect=handoff.ScanError('synthetic unreadable')):
            self.assertEqual(self.bridge.watch(once=True)['status'],'retrying')
            self.assertEqual(self.bridge.watch(once=True)['status'],'retrying')
            self.assertEqual(self.bridge.watch(once=True)['status'],'error')
        self.assertTrue(self.cursor.load()['paused']); self.assertEqual(self.calls(),[])

    def test_second_queue_or_standalone_watcher_cannot_acquire_cursor(self):
        self.delivery()
        for suffix in ('.queue','.watcher'):
            with self.cursor.guard(suffix,nonblock=True):
                with self.assertRaises(handoff.HandoffError): self.bridge.watch(once=True)
        self.assertFalse(self.cursor.load()['paused']); self.assertEqual(self.calls(),[])
        self.assertEqual(list((self.root/'reviews').iterdir()),[])

    def test_corrupt_journal_is_preserved_and_no_call(self):
        (self.runtime/'queue.json').write_text('broken')
        with self.assertRaises(ValueError): self.bridge.watch(once=True)
        self.assertEqual((self.runtime/'queue.json').read_text(),'broken'); self.assertEqual(self.calls(),[])

    def test_missing_journal_with_evidence_cannot_reset_dedup(self):
        self.delivery(); self.bridge.watch(once=True); (self.runtime/'queue.json').unlink()
        with self.assertRaisesRegex(handoff.HandoffError,'journal is missing'): self.bridge.watch(once=True)
        self.assertEqual(len(self.calls()),1)

    def test_changed_config_cli_skill_and_wrong_runtime_identity_stop(self):
        for which in ('config','cli','skill'):
            with self.subTest(which=which):
                c=QueueTests(); c.setUp()
                try:
                    c.delivery()
                    p={'config':c.config,'cli':c.fake,'skill':c.instructions}[which]
                    p.write_text(p.read_text()+'\n')
                    with self.assertRaisesRegex(handoff.HandoffError,'settings changed'): c.bridge.watch(once=True)
                    self.assertEqual(c.calls(),[])
                finally: c.doCleanups()
        self.bridge.watch(once=True); self.c['thread']='00000000-0000-4000-8000-000000000020'; self.configure()
        with self.assertRaisesRegex(handoff.HandoffError,'identity'): self.bridge.watch(once=True)

    def test_clock_backwards_pauses_and_does_not_resend(self):
        self.delivery(); self.bridge.watch(once=True)
        j=self.journal(); j['attempts'][j['active']]['submitted_epoch']=time.time()+100
        self.bridge.save(j)
        with self.assertRaisesRegex(handoff.HandoffError,'Clock'): self.bridge.watch(once=True)
        self.assertEqual(len(self.calls()),1)

    def test_peer_lock_preserved_and_desktop_notice_fallback(self):
        self.c['desktop_notifications']=True; self.configure()
        self.delivery(); self.bridge.watch(once=True); self.expire()
        w=handoff.Writer(self.root); t=w.acquire('peer','do not break')
        try:
            with patch.object(qb,'desktop_notice',return_value={'status':'submitted'}) as notice:
                r=self.bridge.watch(once=True)
                self.assertEqual(r['notification']['peer']['status'],'failed')
                self.assertEqual(r['notification']['desktop']['status'],'submitted'); notice.assert_called_once()
            w.check('peer',t)
        finally: w.release('peer',t)
        r=qb.QueueBridge(self.config).watch(once=True)
        self.assertEqual(r['notification']['peer']['status'],'published')
        self.assertEqual(len(self.calls()),1)

    def test_original_failure_survives_notification_error(self):
        self.delivery(); self.mode('fail')
        with patch.object(self.bridge,'notify',side_effect=OSError('synthetic notification failure')):
            with self.assertRaisesRegex(handoff.HandoffError,'Queue command failed'): self.bridge.watch(once=True)
        self.assertIn('Queue command failed',self.active()['error'])

    def test_normal_pause_wording_does_not_claim_fault_or_review_completion(self):
        self.cursor.control(True,'Human chose pause')
        r=self.bridge.watch(once=True)
        p=r['notification']['peer']['report']['path']; data=(self.root/p).read_text()
        self.assertIn('监听已暂停',data); self.assertNotIn('# ForgeDuet 交接需核对',data)
        self.assertEqual(self.calls(),[])

    def test_finite_explicit_timeouts_and_uuid_required(self):
        for key in ('interval','queue_timeout_seconds','ack_timeout_seconds'):
            for value in (None,0,-1,True,float('inf'),float('nan')):
                c=dict(self.c); c[key]=value; self.config.write_text(json.dumps(c))
                with self.assertRaises(handoff.HandoffError): qb.QueueBridge(self.config)
        c=dict(self.c); c['thread']='a project name'; self.config.write_text(json.dumps(c))
        with self.assertRaises(ValueError): qb.QueueBridge(self.config)

    def test_symlink_cursor_or_instructions_rejected(self):
        p=self.area/'link.md'; p.symlink_to(self.instructions)
        self.c['instructions']=str(p); self.config.write_text(json.dumps(self.c))
        with self.assertRaises(handoff.HandoffError): qb.QueueBridge(self.config)

    def test_persistent_loop_really_waits_then_exits_on_external_pause(self):
        proc=subprocess.Popen([sys.executable,str(ROOT/'scripts/queue_bridge.py'),'watch','--config',str(self.config)],
                              stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        try:
            end=time.monotonic()+4
            while self.cursor.load().get('watcher') is None and time.monotonic()<end: time.sleep(.02)
            self.assertIsNone(proc.poll()); self.assertEqual(self.calls(),[])
            self.cursor.control(True,'External synthetic pause')
            out,err=proc.communicate(timeout=4)
            self.assertEqual(proc.returncode,3,err)
            self.assertEqual(json.loads(out)['status'],'paused')
            self.assertIsNone(self.cursor.load()['watcher'])
        finally:
            if proc.poll() is None: proc.kill(); proc.communicate()

    def test_hard_kill_after_cli_start_does_not_resend_on_restart(self):
        self.delivery(); self.mode('hang')
        proc=subprocess.Popen([sys.executable,str(ROOT/'scripts/queue_bridge.py'),'watch','--config',str(self.config)],
                              stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        pid=None
        try:
            end=time.monotonic()+4
            while time.monotonic()<end:
                files=list(self.runtime.glob('dispatch-*/child.json'))
                if files and self.calls():
                    pid=json.loads(files[0].read_text())['pid']; break
                time.sleep(.01)
            self.assertIsNotNone(pid)
            proc.kill(); proc.communicate(timeout=4)
            # This PID/group is our explicitly spawned fake child, not an unrelated process.
            os.killpg(pid,signal.SIGKILL)
            self.assertEqual(self.active()['status'],'dispatching')
            self.assertEqual(qb.QueueBridge(self.config).watch(once=True)['status'],'needs_recovery')
            self.assertEqual(len(self.calls()),1); self.assertEqual(self.cursor.load()['seen'],{})
        finally:
            if proc.poll() is None: proc.kill(); proc.communicate()
            if pid is not None:
                try: os.killpg(pid,signal.SIGKILL)
                except ProcessLookupError: pass

    def test_foreground_service_process_dispatches_only_on_delivery_and_keeps_waiting(self):
        proc=subprocess.Popen([sys.executable,str(ROOT/'scripts/queue_bridge.py'),'watch','--config',str(self.config)],
                              stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        try:
            end=time.monotonic()+4
            while self.cursor.load().get('watcher') is None and time.monotonic()<end: time.sleep(.01)
            self.assertEqual(self.calls(),[])
            e=self.delivery()
            end=time.monotonic()+4
            while time.monotonic()<end:
                if (self.runtime/'queue.json').exists():
                    j=self.journal(); a=j['attempts'].get(j['active'],{})
                    if a.get('status')=='submitted': break
                time.sleep(.01)
            self.assertEqual(self.active()['status'],'submitted')
            self.publish_review(self.active()); self.cursor.ack(e['path'],e['sha256'])
            end=time.monotonic()+4
            while self.journal()['active'] is not None and time.monotonic()<end: time.sleep(.01)
            self.assertIsNone(self.journal()['active']); self.assertIsNone(proc.poll())
            self.assertEqual(len(self.calls()),1)
            self.cursor.control(True,'Synthetic run ended')
            out,err=proc.communicate(timeout=4); self.assertEqual(proc.returncode,3,err)
            results=[json.loads(s) for s in out.splitlines()]
            self.assertEqual([r['status'] for r in results],['submitted','handled','paused'])
        finally:
            if proc.poll() is None: proc.kill(); proc.communicate()


if __name__=='__main__': unittest.main()
