import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import git_transport as gt
import handoff


class GitTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory(prefix='fd-git-fixture-');self.addCleanup(t.cleanup);self.area=Path(t.name).resolve()
        self.remote=self.area/'remote.git'
        subprocess.run(['git','init','--bare','-q',str(self.remote)],check=True)
        self.clients={}
        for role in ('build','review'):
            root=self.area/role;root.mkdir();box=root/'handoff';box.mkdir();runtime=root/'runtime';runtime.mkdir()
            for folder in ('deliveries','reviews','review-tests'):(box/folder).mkdir()
            config=root/'config.json';config.write_text(json.dumps(dict(schema=1,role=role,run_id='fixture',remote=str(self.remote),
                            mailbox=str(box),runtime=str(runtime),author='Fixture',email='fixture@example.invalid')))
            self.clients[role]=gt.GitTransport(config)
        self.build=self.clients['build'];self.review=self.clients['review']

    def report(self, client, folder, name='round-1.md', text='Synthetic report'):
        w=handoff.Writer(client.root);token=w.acquire('fixture','publish synthetic input')
        try:return w.publish('fixture',token,folder+'/'+name,text)
        finally:w.release('fixture',token)

    def test_two_machines_bidirectional_and_exact_cursor_ack(self):
        rec=self.report(self.build,'deliveries');self.build.sync()
        cursor=handoff.Cursor(self.review.root/'.runtime.json');cursor.init(self.review.root,'review')
        result=self.review.sync();self.assertEqual(result['received']['imported'],[rec['path']])
        self.assertEqual(cursor.load()['seen'],{})
        self.assertEqual(cursor.check(60)['events'][0]['sha256'],rec['sha256'])
        cursor.ack(rec['path'],rec['sha256'])
        self.report(self.review,'reviews',text='Synthetic feedback')
        (self.review.root/'review-tests/probe.cpp').write_text('int main() { return 0; }')
        self.review.sync();result=self.build.sync()
        self.assertEqual(len(result['received']['imported']),2)
        self.assertEqual((self.build.root/'review-tests/probe.cpp').read_bytes(),(self.review.root/'review-tests/probe.cpp').read_bytes())
        self.assertEqual(self.review.sync()['received']['imported'],[])

    def test_private_files_and_unmarked_reports_never_published(self):
        (self.build.root/'deliveries/draft.md').write_text('not ready')
        (self.build.root/'secret.json').write_text('synthetic private data')
        self.build.sync();self.review.sync()
        self.assertFalse((self.review.root/'deliveries/draft.md').exists())
        self.assertFalse((self.review.root/'secret.json').exists())

    def test_append_new_round_preserves_old_bytes(self):
        rec=self.report(self.build,'deliveries');self.build.sync();self.review.sync()
        self.report(self.build,'deliveries','round-2.md');self.build.sync();self.review.sync()
        self.assertEqual(gt.sha((self.review.root/rec['path']).read_bytes()),rec['sha256'])

    def test_published_report_mutation_is_rejected(self):
        self.report(self.build,'deliveries');self.build.sync()
        (self.build.root/'deliveries/round-1.md').write_text('changed\n交付完成\n')
        with self.assertRaisesRegex(handoff.HandoffError,'removed/changed'):self.build.sync()

    def test_local_collision_is_preserved(self):
        self.report(self.build,'deliveries');self.build.sync()
        p=self.review.root/'deliveries/round-1.md';p.write_text('different local report')
        with self.assertRaisesRegex(handoff.HandoffError,'collision'):self.review.sync()
        self.assertEqual(p.read_text(),'different local report')

    def test_push_failure_retains_same_commit_and_resumes_without_duplicate_commit(self):
        self.report(self.build,'deliveries');original=self.build.git
        def fail(*args,**kwargs):
            if args[0]=='push':raise handoff.HandoffError('synthetic offline')
            return original(*args,**kwargs)
        with patch.object(self.build,'git',side_effect=fail):
            with self.assertRaisesRegex(handoff.HandoffError,'offline'):self.build.sync()
        pending=json.loads(self.build.journal.read_text())['pending'];self.assertIsNotNone(pending)
        self.build=gt.GitTransport(self.build.config);self.build.sync()
        self.assertEqual(self.build.remote_head(self.build.branch),pending)
        self.assertEqual(self.build.git('rev-list','--count',pending).strip(),b'1')

    def test_successful_push_with_lost_receipt_reconciles_without_repush(self):
        self.report(self.build,'deliveries');original=self.build.git
        def lost(*args,**kwargs):
            out=original(*args,**kwargs)
            if args[0]=='push':raise handoff.HandoffError('lost response')
            return out
        with patch.object(self.build,'git',side_effect=lost):
            with self.assertRaises(handoff.HandoffError):self.build.sync()
        def no_push(*args,**kwargs):
            self.assertNotEqual(args[0],'push');return original(*args,**kwargs)
        with patch.object(self.build,'git',side_effect=no_push):self.build.sync()

    def test_unknown_existing_role_branch_cannot_be_adopted(self):
        self.report(self.build,'deliveries');self.build.sync()
        state=json.loads(self.build.journal.read_text());state['own_head']=None;handoff.atomic_json(self.build.journal,state)
        with self.assertRaisesRegex(handoff.HandoffError,'Own branch changed'):self.build.sync()

    def test_peer_mutation_and_history_rewrite_rejected(self):
        self.report(self.build,'deliveries');self.build.sync();self.review.sync()
        head=self.build.remote_head(self.build.branch);files=self.build.snapshot(head,'build');files['deliveries/round-1.md']='bad\n交付完成\n'.encode()
        manifest=dict(schema=1,run_id='fixture',role='build',files={n:gt.sha(d) for n,d in files.items()})
        files[gt.MANIFEST]=json.dumps(manifest).encode();tree=self.build.tree(files)
        commit=self.build.git('commit-tree',tree,'-p',head,data=b'evil mutation').decode().strip()
        self.build.git('push',str(self.remote),commit+':'+self.build.branch)
        with self.assertRaisesRegex(handoff.HandoffError,'rewrote/deleted'):self.review.sync()

    def test_peer_missing_manifest_rejected_without_import(self):
        self.build.sync();tree=self.build.tree({'deliveries/a.md':'hello\n交付完成\n'.encode()})
        commit=self.build.git('commit-tree',tree,data=b'no manifest').decode().strip()
        self.build.git('push',str(self.remote),commit+':'+self.build.branch)
        with self.assertRaisesRegex(handoff.HandoffError,'manifest'):self.review.sync()
        self.assertEqual(list((self.review.root/'deliveries').iterdir()),[])

    def test_symlink_and_path_traversal_rejected(self):
        (self.build.root/'deliveries/bad.md').symlink_to(self.area/'outside')
        with self.assertRaises(handoff.HandoffError):self.build.sync()
        for path in ('../outside','deliveries/../outside','/deliveries/a.md','reviews/a.md','deliveries/.hidden.md'):
            with self.assertRaises(handoff.HandoffError):self.build.path(path,'build')

    def test_duplicate_synchronizer_cannot_enter_guard(self):
        with self.build.guard():
            with self.assertRaisesRegex(handoff.HandoffError,'owns'):self.build.sync()

    def test_auxiliary_files_import_before_completed_reports(self):
        self.report(self.review,'reviews');(self.review.root/'review-tests/probe.py').write_text('pass')
        self.review.sync();order=[];original=os.link
        def link(a,b):order.append(str(b));return original(a,b)
        with patch.object(gt.os,'link',side_effect=link):self.build.sync()
        self.assertIn('review-tests',order[0]);self.assertIn('/reviews/',order[1])

    def test_half_import_can_resume_without_overwriting(self):
        self.report(self.build,'deliveries');self.report(self.build,'deliveries','round-2.md');self.build.sync()
        original=os.link;count=[0]
        def interrupt(a,b):
            count[0]+=1
            if count[0]==2:raise OSError('synthetic interrupted import')
            return original(a,b)
        with patch.object(gt.os,'link',side_effect=interrupt):
            with self.assertRaises(OSError):self.review.sync()
        self.review=gt.GitTransport(self.review.config);self.review.sync()
        self.assertEqual(len(list((self.review.root/'deliveries').glob('*.md'))),2)

    def test_conflicting_remote_writer_never_force_pushes(self):
        self.report(self.build,'deliveries');self.build.sync()
        state=self.build.load();self.build.git('push',str(self.remote),':'+self.build.branch)
        with self.assertRaisesRegex(handoff.HandoffError,'Own branch changed'):self.build.sync()

    def test_config_and_blob_limits_are_enforced(self):
        self.build.c['max_bytes']=3
        self.report(self.build,'deliveries')
        with self.assertRaisesRegex(handoff.HandoffError,'Oversized'):self.build.sync()
        c=json.loads(self.review.config.read_text());c['run_id']='changed';self.review.config.write_text(json.dumps(c))
        with self.assertRaisesRegex(handoff.HandoffError,'config changed'):self.review.sync()

    def test_stop_notice_is_deduplicated_and_not_a_review(self):
        with patch.object(gt,'desktop_notice',return_value={'status':'sent'}) as os_notice:
            first=self.build.notify('synthetic offline')
            second=self.build.notify('synthetic offline')
        self.assertEqual(first,second);self.assertEqual(os_notice.call_count,1)
        notices=list((self.build.root/'reviews').glob('git-transport-*.md'))
        self.assertEqual(len(notices),1)
        self.assertIn('review_verdict: null',notices[0].read_text())
        self.assertEqual(first['model_calls'],0)

    def test_peer_history_rewind_is_not_silently_accepted(self):
        self.report(self.build,'deliveries');self.build.sync();first=self.build.remote_head(self.build.branch)
        self.report(self.build,'deliveries','round-2.md');self.build.sync();self.review.sync()
        subprocess.run(['git','--git-dir='+str(self.remote),'update-ref',self.build.branch,first],check=True)
        with self.assertRaises(handoff.HandoffError):self.review.sync()
        self.assertTrue((self.review.root/'deliveries/round-2.md').exists())
