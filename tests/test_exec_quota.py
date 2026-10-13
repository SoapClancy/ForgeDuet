import json
from pathlib import Path
import sys
import time
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import handoff
import quota
import markdown_bridge as mb
import relay
import test_markdown_bridge as fixtures
import test_relay as relay_fixtures


class ExecQuotaTests(unittest.TestCase):
    def setUp(self):
        self.f=fixtures.MarkdownBridgeTests();self.f.setUp();self.addCleanup(self.f.doCleanups)
        self.input=self.f.delivery();self.f.mode('quota')

    def test_typed_prework_quota_wait_then_new_turn_preserves_input(self):
        result=self.f.bridge.watch(once=True);self.assertEqual(result['status'],'waiting_quota')
        prior=json.loads(self.f.bridge.journal.read_text());self.assertFalse(self.f.cursor.load()['paused'])
        for _ in range(5):self.assertEqual(self.f.bridge.watch(once=True)['status'],'waiting_quota')
        self.assertEqual(len(self.f.calls()),1);self.assertEqual(self.f.cursor.load()['seen'],{})
        self.f.mode('ok');self.f.bridge=mb.Bridge(str(self.f.config))
        with patch.object(time,'time',return_value=prior['quota']['resets_at']+3):result=self.f.bridge.watch(once=True)
        self.assertEqual(result['status'],'handled');self.assertEqual(len(self.f.calls()),2)
        self.assertEqual(self.f.cursor.load()['seen'][self.input['path']],self.input['sha256'])
        self.assertEqual(len(list(self.f.runtime.glob('*-run-*/attempt.json'))),2)

    def test_any_partial_item_forbids_ephemeral_replay(self):
        self.f.mode('quota_started')
        with self.assertRaises(handoff.HandoffError):self.f.bridge.watch(once=True)
        self.assertTrue(self.f.cursor.load()['paused']);self.assertEqual(len(self.f.calls()),1)

    def test_missing_reset_time_is_gated_without_probing(self):
        self.f.mode('quota_unknown')
        with self.assertRaises(quota.QuotaError):self.f.bridge.watch(once=True)
        self.assertTrue(self.f.cursor.load()['paused']);self.assertEqual(len(self.f.calls()),1)

    def test_state_changes_during_wait_require_reconciliation(self):
        self.f.bridge.watch(once=True);self.f.state.write_text('changed rules')
        with self.assertRaisesRegex(handoff.HandoffError,'State changed'):self.f.bridge.watch(once=True)
        self.assertEqual(len(self.f.calls()),1)

    def test_plain_capacity_or_billing_errors_are_not_quota_receipts(self):
        path=self.f.area/'error.jsonl'
        for error in ({'message':'usage limit reached; reset soon'},{'code':'insufficient_quota','resets_at':time.time()+50},{'code':'server_overloaded','resets_at':time.time()+50}):
            path.write_text(json.dumps({'type':'turn.failed','error':error}))
            self.assertIsNone(quota.before_work_jsonl(path,'event','model'))


class AdapterQuotaIntegrationTests(unittest.TestCase):
    def test_exited_adapter_waits_then_continues_same_job_to_candidate(self):
        f=relay_fixtures.RelayTests();f.setUp();self.addCleanup(f.doCleanups)
        result=f.result('candidate','build');(f.area/'result-template.json').write_text(json.dumps(result))
        adapter=f.area/'synthetic-adapter.py'
        adapter.write_text('''import sys,json,pathlib,time
job=json.loads(pathlib.Path(sys.argv[1]).read_text());out=pathlib.Path(sys.argv[2])
if job.get('quota_continuation'):
 out.write_text((pathlib.Path(__file__).parent/'result-template.json').read_text())
else:
 now=time.time();out.write_text(json.dumps(dict(schema=1,status='quota_exhausted',event_id=job['message']['id'],model=job['settings']['model'],receipt_id='adapter-quota-1',observed_at=now,resets_at=now+50,terminal=True,resume_safe=True,source='synthetic adapter after stopped worker',usage=dict(tokens=0,usd=0))))
 sys.exit(75)
''')
        f.cfg['roles']['build']['adapter_argv']=[sys.executable,str(adapter)]
        box=f.init();f.task();claim=box.claim('build','fixture');relay.run_claim(box,'build',claim)
        job=box.status()['jobs'][claim['id']];self.assertEqual(job['status'],'waiting_quota')
        self.assertIsNone(box.claim('build','early'))
        with patch.object(time,'time',return_value=job['quota']['resets_at']+3):
            resumed=box.claim('build','after');relay.run_claim(box,'build',resumed)
        self.assertEqual(box.status()['jobs'][claim['id']]['status'],'done')
        self.assertIsNotNone(box.claim('review','reviewer'))
