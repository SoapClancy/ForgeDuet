import json
from pathlib import Path
import sys
import time
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import handoff
import quota
import relay
import test_relay as relay_fixtures
import test_queue_bridge as queue_fixtures


def make_receipt(event,model,**extra):
    now=time.time()
    return dict(schema=1,status='quota_exhausted',event_id=event,model=model,receipt_id='receipt-1',
                observed_at=now,resets_at=now+50,terminal=True,resume_safe=True,source='synthetic typed client error',**extra)


class RelayQuotaTests(unittest.TestCase):
    def setUp(self):
        self.f=relay_fixtures.RelayTests();self.f.setUp();self.addCleanup(self.f.doCleanups)
        self.box=self.f.init();self.f.task();self.claim=self.box.claim('build','fixture')

    def defer(self,**extra):
        q=make_receipt(self.claim['id'],'fixture-model');q.update(extra)
        self.box.defer_quota(self.claim['id'],self.claim['token'],q);return q

    def test_waits_across_restart_then_same_task_claim_continues(self):
        q=self.defer();self.assertIsNone(self.box.claim('build','early'))
        box=relay.Mailbox(self.box.path)
        with patch.object(relay.time,'time',return_value=q['resets_at']+3):
            claim=box.claim('build','after-reset')
        self.assertEqual(claim['id'],self.claim['id']);self.assertNotEqual(claim['token'],self.claim['token'])
        payload=json.loads(Path(claim['job_file']).read_text());self.assertEqual(payload['quota_continuation']['receipt_id'],q['receipt_id'])
        self.assertEqual(payload['message']['id'],self.claim['id'])

    def test_user_pause_never_auto_resumes(self):
        q=self.defer();self.box.pause('user stop')
        with patch.object(relay.time,'time',return_value=q['resets_at']+3):self.assertIsNone(self.box.claim('build','after'))
        self.assertEqual(self.box.status()['phase'],'needs_human')

    def test_unknown_reset_and_unsafe_receipts_rejected(self):
        for change in ({'resets_at':None},{'terminal':False},{'resume_safe':False},{'event_id':'other'},{'model':'other'}):
            q=make_receipt(self.claim['id'],'fixture-model');q.update(change)
            with self.assertRaises(quota.QuotaError):self.box.defer_quota(self.claim['id'],self.claim['token'],q)

    def test_budget_is_not_provider_quota_and_still_blocks(self):
        # Configure a new capped fixture before initialization.
        self.f.doCleanups();self.f=relay_fixtures.RelayTests();self.f.setUp();self.addCleanup(self.f.doCleanups)
        self.f.cfg['budgets']['tokens']=10;self.box=self.f.init();self.f.task();self.claim=self.box.claim('build','fixture')
        q=self.defer(usage={'tokens':10,'usd':0})
        with patch.object(relay.time,'time',return_value=q['resets_at']+3):self.assertIsNone(self.box.claim('build','after'))
        self.assertIn('budget',self.box.status()['reason'])

    def test_review_role_uses_same_default_quota_policy(self):
        # Build a review job using fixture's real validated candidate response.
        self.f.finish(self.claim,self.f.result('candidate','build'))
        review_claim=self.box.claim('review','reviewer')
        q=make_receipt(review_claim['id'],'fixture-model')
        self.box.defer_quota(review_claim['id'],review_claim['token'],q)
        self.assertIsNone(self.box.claim('review','early'))
        with patch.object(relay.time,'time',return_value=q['resets_at']+3):self.assertIsNotNone(self.box.claim('review','after'))


class QueueQuotaTests(unittest.TestCase):
    def setUp(self):
        self.f=queue_fixtures.QueueTests();self.f.setUp();self.addCleanup(self.f.doCleanups)
        self.status=self.f.area/'quota.json';self.f.c['quota_status_file']=str(self.status);self.f.configure()
        self.f.delivery();self.f.bridge.watch(once=True);a=self.f.active()
        self.q=make_receipt(a['key'],self.f.c['model'],message_id=a['message_id'])
        self.status.write_text(json.dumps(self.q))

    def test_wait_is_model_free_and_restart_continues_once(self):
        for _ in range(5):self.assertEqual(self.f.bridge.watch(once=True)['status'],'waiting_quota')
        self.assertEqual(len(self.f.calls()),1)
        self.f.configure()
        with patch.object(time,'time',return_value=self.q['resets_at']+3):
            result=self.f.bridge.watch(once=True)
            for _ in range(3):self.assertEqual(self.f.bridge.watch(once=True)['status'],'awaiting_ack')
        self.assertTrue(result['continuation']);self.assertEqual(len(self.f.calls()),2)
        self.assertEqual(self.f.cursor.load()['seen'],{})

    def test_ack_and_bound_review_wins_over_old_quota_receipt(self):
        a=self.f.active();self.f.publish_review(a);self.f.cursor.ack(a['event']['path'],a['event']['sha256'])
        self.assertEqual(self.f.bridge.watch(once=True)['status'],'handled');self.assertEqual(len(self.f.calls()),1)

    def test_manual_pause_wins_over_reset(self):
        self.f.bridge.watch(once=True);self.f.cursor.control(True,'user pause')
        with patch.object(time,'time',return_value=self.q['resets_at']+3):self.assertEqual(self.f.bridge.watch(once=True)['status'],'paused')
        self.assertEqual(len(self.f.calls()),1)

    def test_wrong_message_stops_without_retry(self):
        self.q['message_id']='not-this-message';self.status.write_text(json.dumps(self.q))
        with self.assertRaises(handoff.HandoffError):self.f.bridge.watch(once=True)
        self.assertEqual(len(self.f.calls()),1)

    def test_uncertain_resume_does_not_retry_after_restart(self):
        self.f.mode('fail')
        with patch.object(time,'time',return_value=self.q['resets_at']+3):
            with self.assertRaises(handoff.HandoffError):self.f.bridge.watch(once=True)
        self.assertEqual(len(self.f.calls()),2)
        with patch.object(time,'time',return_value=self.q['resets_at']+3):
            self.f.configure();self.assertEqual(self.f.bridge.watch(once=True)['status'],'error')
            self.assertEqual(self.f.active()['status'],'uncertain');self.assertTrue(self.f.cursor.load()['paused'])
        self.assertEqual(len(self.f.calls()),2)

    def test_delivery_mutation_during_quota_wait_is_not_resumed(self):
        self.f.bridge.watch(once=True)
        (self.f.root/'deliveries/r1.md').write_text('different\n交付完成\n')
        with patch.object(time,'time',return_value=self.q['resets_at']+3):
            with self.assertRaises(handoff.HandoffError):self.f.bridge.watch(once=True)
        self.assertEqual(len(self.f.calls()),1)
