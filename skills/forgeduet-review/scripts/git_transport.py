#!/usr/bin/env python3
"""Append-only Git handoff channels. No checkout, candidate hooks or model calls.

Each role has a remote branch. Local cursors/locks/updates.log stay local.
Ordinary fast-forward pushes are the cross-machine serialization boundary.
"""
import argparse
import contextlib
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import time
from urllib.parse import urlsplit, unquote

from handoff import Writer, HandoffError, atomic_json, complete, inside, require, root_path
from markdown_bridge import desktop_notice

OWN = {'build': {'deliveries'}, 'review': {'reviews', 'review-tests'}}
MANIFEST = 'handoff-manifest.json'


class RetryableGitError(HandoffError):
    """Only a recognized remote-connectivity failure, never integrity/auth."""


def local_only(name):
    # Reserved on both channels, including notices from the earlier candidate.
    return re.fullmatch(r'git-transport-(?:response-)?[0-9a-f]{64}\.md', PurePosixPath(name).name) is not None


def sha(data):
    return hashlib.sha256(data).hexdigest()


class GitTransport:
    def __init__(self, config):
        self.config = Path(config).resolve(strict=True)
        c = json.loads(self.config.read_text())
        required = {'schema', 'role', 'run_id', 'remote', 'mailbox', 'runtime', 'author', 'email'}
        require(isinstance(c, dict) and set(c) <= required | {'interval', 'timeout', 'max_bytes', 'desktop_notifications', 'max_network_errors', 'retry_max_seconds'} and required <= set(c), 'Invalid Git transport config')
        require(type(c['schema']) is int and c['schema'] == 1 and c['role'] in OWN and isinstance(c['run_id'],str) and re.fullmatch(r'[A-Za-z0-9_-]{1,80}', c['run_id']), 'Invalid role/run ID')
        for field in ('remote', 'author', 'email'):
            require(isinstance(c[field], str) and c[field] and '\n' not in c[field] and not c[field].startswith('-'), 'Invalid '+field)
        c.setdefault('desktop_notifications', True)
        require(type(c['desktop_notifications']) is bool, 'Expected boolean desktop_notifications')
        remote = c['remote']
        if remote.startswith('https://'):
            require(urlsplit(remote).username is None and urlsplit(remote).password is None, 'Use credential helpers, not credentials embedded in remote URL')
        require(remote.startswith(('https://', 'ssh://', 'file://', '/')) or re.fullmatch(r'[^@\s:]+@[^\s:]+:[^\s]+', remote), 'Use explicit HTTPS/SSH or local fixture remote')
        for field, default in [('interval', 60), ('timeout', 30), ('max_bytes', 16 * 1024 * 1024),
                               ('max_network_errors', 5), ('retry_max_seconds', 300)]:
            c.setdefault(field, default)
            require(type(c[field]) is int and c[field] > 0, 'Positive integer '+field+' required')
        self.c = c
        self.root = root_path(c['mailbox'])
        self.runtime = root_path(c['runtime'])
        require(not self.runtime.is_relative_to(self.root) and not self.root.is_relative_to(self.runtime), 'Separate private runtime and mailbox')
        require(not self.config.is_relative_to(self.root), 'Trusted config must be outside mailbox')
        self.store = self.runtime / 'objects.git'
        self.journal = self.runtime / 'git-transport.json'
        self.identity = {'config_sha256': sha(self.config.read_bytes()), 'config': str(self.config)}
        self.branch = 'refs/heads/forgeduet/'+c['run_id']+'/'+c['role']
        peer = 'review' if c['role'] == 'build' else 'build'
        self.peer = peer
        self.peer_branch = 'refs/heads/forgeduet/'+c['run_id']+'/'+peer

    def transient(self, diagnostics):
        text = diagnostics.lower()
        permanent = ('authentication failed', 'permission denied', 'access denied',
                     'could not read username', 'non-fast-forward', '[rejected]',
                     '[remote rejected]', 'repository not found', 'http 401', 'http 403')
        if any(item in text for item in permanent):
            return False
        remote = self.c['remote']
        path = (Path(remote) if remote.startswith('/') else
                Path(unquote(urlsplit(remote).path)) if remote.startswith('file://') else None)
        # A temporarily moved/unmounted local fixture/share is also recoverable.
        if path is not None and not path.exists():
            return True
        return any(item in text for item in (
            'could not resolve host', 'could not resolve hostname', 'temporary failure in name resolution',
            'failed to connect', 'connection refused', 'connection timed out', 'connection reset',
            'connection closed', 'network is unreachable', 'no route to host', 'remote end hung up',
            'early eof', 'http 502', 'http 503', 'http 504', 'returned error: 502',
            'returned error: 503', 'returned error: 504', 'operation timed out'))

    def git(self, *args, data=None, ok=(0,)):
        env = {k:v for k,v in os.environ.items() if not k.startswith('GIT_')}
        env.update(GIT_TERMINAL_PROMPT='0', GIT_AUTHOR_NAME=self.c['author'], GIT_AUTHOR_EMAIL=self.c['email'],
                   GIT_COMMITTER_NAME=self.c['author'], GIT_COMMITTER_EMAIL=self.c['email'], LC_ALL='C')
        command = ['git', '--git-dir='+str(self.store), '-c', 'core.hooksPath=/dev/null', '-c', 'commit.gpgsign=false',
                   '-c', 'protocol.ext.allow=never', '-c', 'gc.auto=0', '-c', 'maintenance.auto=false', '-c', 'credential.interactive=false'] + list(args)
        network = args[0] in ('ls-remote', 'fetch', 'push')
        try:
            p = subprocess.run(command, input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               env=env, timeout=self.c['timeout'])
        except subprocess.TimeoutExpired as exc:
            if network:
                raise RetryableGitError('Remote Git operation timed out; retain transfer intent: '+args[0]) from exc
            raise
        if p.returncode not in ok:
            detail = p.stderr.decode(errors='replace')[:800]
            error = RetryableGitError if network and self.transient(detail) else HandoffError
            raise error('Git operation failed; retain state: '+detail)
        return p.stdout

    @contextlib.contextmanager
    def guard(self):
        require(not (self.runtime/'transport.guard').is_symlink(), 'Symlink guard')
        with (self.runtime/'transport.guard').open('a') as f:
            try: fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError: raise HandoffError('Another local Git synchronizer owns this runtime')
            try: yield
            finally: fcntl.flock(f.fileno(), fcntl.LOCK_UN)

    def load(self):
        require(sha(self.config.read_bytes()) == self.identity['config_sha256'], 'Git config changed; reconcile')
        require(not self.store.is_symlink() and not self.journal.is_symlink(), 'Symlink runtime')
        if not self.journal.exists():
            require(not self.store.exists(), 'Objects without journal; preserve and reconcile')
            self.git('init', '--bare', '--template=', str(self.store))
            state = {'schema':1, 'identity':self.identity, 'own_head':None, 'peer_head':None, 'pending':None}
            atomic_json(self.journal, state)
        state = json.loads(self.journal.read_text())
        require(state.get('schema') == 1 and state.get('identity') == self.identity, 'Wrong/corrupt Git transport state')
        for field in ('own_head','peer_head','pending'):
            require(field in state and (state[field] is None or re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}',state[field])), 'Invalid stored head')
        return state

    def remote_head(self, branch):
        out = self.git('ls-remote', '--refs', self.c['remote'], branch).decode().strip()
        if not out: return None
        parts = out.split()
        require(len(parts)==2 and parts[1]==branch and re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}',parts[0]), 'Unexpected remote ref')
        return parts[0]

    def fetch(self, branch, head, local):
        self.git('fetch', '--no-tags', '--no-write-fetch-head', self.c['remote'], branch+':'+local)
        actual = self.git('rev-parse', local).decode().strip()
        # If the writer advanced between discovery and fetch, validate the actual fetched head instead.
        require(re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', actual), 'Invalid fetched commit')
        return actual

    def path(self, name, role):
        p = PurePosixPath(name)
        require(isinstance(name,str) and not p.is_absolute() and len(p.parts)>=2 and p.parts[0] in OWN[role]
                and all(part not in ('','.', '..') and not part.startswith('.') for part in p.parts)
                and p.as_posix()==name and '\\' not in name and '\n' not in name and '\r' not in name, 'Forbidden handoff path: '+str(name))
        require(p.parts[0]=='review-tests' or (len(p.parts)==2 and p.suffix=='.md'), 'Report paths must be one Markdown file')
        return name

    def snapshot(self, commit, role):
        if commit is None: return {}
        out = self.git('ls-tree', '-rz', commit)
        entries = {}
        for entry in out.split(b'\0'):
            if not entry: continue
            meta, raw = entry.split(b'\t',1); mode, kind, obj = meta.decode().split(); name=raw.decode('utf-8')
            require(mode=='100644' and kind=='blob', 'No symlinks, executable modes or submodules in handoff')
            if name!=MANIFEST:self.path(name,role)
            size=int(self.git('cat-file','-s',obj));require(size<=self.c['max_bytes'],'Oversized handoff blob')
            entries[name]=self.git('cat-file','blob',obj)
            require(sum(map(len,entries.values()))<=self.c['max_bytes'],'Oversized handoff snapshot')
        require(MANIFEST in entries,'Missing handoff manifest')
        manifest=json.loads(entries.pop(MANIFEST))
        expected={'schema':1,'run_id':self.c['run_id'],'role':role,'files':{n:sha(d) for n,d in sorted(entries.items())}}
        require(manifest==expected,'Wrong run/role/hash manifest')
        for n,d in entries.items():
            require(not local_only(n), 'Local-only transport notice/response in remote snapshot; reconcile legacy channel')
            if n.split('/')[0]!='review-tests':require(complete(d),'Incomplete peer report')
        return entries

    def local_snapshot(self):
        files={}
        for folder in OWN[self.c['role']]:
            top=inside(self.root,folder)
            if not top.exists():continue
            for p in sorted(top.rglob('*')):
                require(not p.is_symlink(),'Symlink local handoff')
                if not p.is_file():continue
                rel=p.relative_to(self.root).as_posix()
                if any(x.startswith('.') for x in p.relative_to(top).parts):continue
                if local_only(rel):continue
                self.path(rel,self.c['role'])
                require(p.stat().st_size<=self.c['max_bytes'],'Oversized local handoff')
                data=p.read_bytes()
                if folder!='review-tests' and not complete(data):continue
                files[rel]=data
        require(sum(map(len,files.values()))<=self.c['max_bytes'],'Oversized local snapshot')
        return files

    def tree(self, files):
        # Construct trees with plumbing; never touch a product checkout/index.
        entries={}
        for name,data in files.items():
            parts=PurePosixPath(name).parts;level=entries
            for part in parts[:-1]: level=level.setdefault(part,{})
            require(parts[-1] not in level,'Path collision')
            level[parts[-1]]=self.git('hash-object','-w','--stdin',data=data).decode().strip()
        def make(level):
            rows=[]
            for name,value in sorted(level.items()):
                if isinstance(value,dict):mode,kind,obj='040000','tree',make(value)
                else:mode,kind,obj='100644','blob',value
                rows.append((mode+' '+kind+' '+obj+'\t'+name).encode()+b'\0')
            return self.git('mktree','-z',data=b''.join(rows)).decode().strip()
        return make(entries)

    def publish(self, state):
        remote=self.remote_head(self.branch)
        if state['pending']:
            pending=state['pending']
            if remote!=pending:
                require(remote==state['own_head'],'Remote writer diverged while push outcome uncertain')
                self.git('push','--porcelain',self.c['remote'],pending+':'+self.branch)
                require(self.remote_head(self.branch)==pending,'Push outcome uncertain; retain pending commit')
            state['own_head'],state['pending']=pending,None;atomic_json(self.journal,state)
            return {'status':'published','head':pending}
        require(self.remote_head(self.branch)==state['own_head'],'Own branch changed or journal missing; no force push/adoption')
        previous=self.snapshot(state['own_head'],self.c['role']);current=self.local_snapshot()
        require(all(current.get(n)==d for n,d in previous.items()),'Published local reports removed/changed; supersede with a new file')
        if current==previous:return {'status':'unchanged','head':state['own_head']}
        manifest={'schema':1,'run_id':self.c['run_id'],'role':self.c['role'],'files':{n:sha(d) for n,d in sorted(current.items())}}
        tree=self.tree(dict(current,**{MANIFEST:json.dumps(manifest,sort_keys=True,ensure_ascii=False).encode()}))
        args=['commit-tree',tree]
        if state['own_head']:args+=['-p',state['own_head']]
        commit=self.git(*args,data=b'ForgeDuet immutable handoff snapshot\n').decode().strip()
        self.git('update-ref','refs/forgeduet/outgoing',commit)
        state['pending']=commit;atomic_json(self.journal,state)
        # Same exact commit may be re-pushed after a network failure; no model work is retried.
        return self.publish(state)

    def receive(self,state):
        remote=self.remote_head(self.peer_branch)
        if remote is None:
            require(state['peer_head'] is None,'Peer branch disappeared; reconcile')
            return {'status':'waiting','imported':[]}
        head=self.fetch(self.peer_branch,remote,'refs/forgeduet/peer')
        if state['peer_head']:
            self.git('merge-base','--is-ancestor',state['peer_head'],head)
        old=self.snapshot(state['peer_head'],self.peer);new=self.snapshot(head,self.peer)
        require(all(new.get(n)==d for n,d in old.items()),'Peer rewrote/deleted immutable handoff')
        for n,d in new.items():
            p=inside(self.root,n)
            require(not p.exists() or (p.is_file() and p.read_bytes()==d),'Local/peer report collision; preserve both')
        w=Writer(self.root);owner='git-sync / '+self.c['role'];token=w.acquire(owner,'import verified peer Git handoff')
        imported=[]
        try:
            # Auxiliary evidence first, completion-marked reports last.
            for n,d in sorted(new.items(),key=lambda item:(not item[0].startswith('review-tests/'),item[0])):
                p=inside(self.root,n)
                if p.exists():
                    require(p.read_bytes()==d,'Report changed during import');continue
                p.parent.mkdir(parents=True,exist_ok=True)
                p=inside(self.root,n)
                temp=p.parent/('.git-import-'+sha(d)+'.tmp')
                require(not temp.is_symlink(),'Symlink import temporary')
                with temp.open('wb') as f:f.write(d);f.flush();os.fsync(f.fileno())
                try:os.link(str(temp),str(p))
                finally:temp.unlink()
                fd=os.open(str(p.parent),os.O_RDONLY)
                try:os.fsync(fd)
                finally:os.close(fd)
                imported.append(n)
            if imported:w.log(owner,token,'Imported peer commit '+head+': '+json.dumps(imported,ensure_ascii=False))
            state['peer_head']=head;atomic_json(self.journal,state)
        finally:w.release(owner,token)
        return {'status':'imported' if imported else 'unchanged','head':head,'imported':imported}

    def notify(self, error):
        detail={'status':'needs_human','error':str(error),'role':self.c['role'],'run_id':self.c['run_id']}
        retry_path=self.runtime/'network-retry.json'
        if retry_path.exists() and not retry_path.is_symlink():
            try:
                retry=json.loads(retry_path.read_text())
                if retry.get('stopped'):detail['network_incident']=retry.get('incident',0)
            except (OSError,ValueError):pass
        key=sha(json.dumps(detail,sort_keys=True).encode())
        path=self.runtime/('notice-'+key+'.json')
        require(not path.is_symlink(),'Symlink notice receipt')
        old=json.loads(path.read_text()) if path.exists() else {}
        if old:
            require(old.get('detail')==detail,'Wrong notice receipt identity; preserve it')
        result={'schema':2,'detail':detail,'model_calls':0}
        if old.get('schema')==2:
            result.update({k:old[k] for k in ('desktop','local_errors') if k in old})
        elif old:
            result['legacy_receipt']=old
        local=old.get('local')
        if local:
            target=inside(self.root,local['path'])
            require(target.is_file() and complete(target.read_bytes()) and sha(target.read_bytes())==local['sha256'],
                    'Previously published local notice changed/missing; reconcile')
            return old  # Only successful durable local publication completes dedup.
        w=Writer(self.root);owner='git-sync / '+self.c['role'];token=None
        try:
            token=w.acquire(owner,'record stopped Git transport')
            # Wake this machine's role, not the remote role. Never export this namespace.
            folder='reviews' if self.c['role']=='build' else 'deliveries'
            name=folder+'/git-transport-'+key+'.md'
            target=inside(self.root,name)
            if target.exists():
                text=target.read_text()
                require(complete(target.read_bytes()) and 'transport_scope: local' in text.splitlines()
                        and json.dumps(detail,ensure_ascii=False) in text.splitlines(),'Conflicting transport notice')
                result['local']={'path':name,'sha256':sha(target.read_bytes())}
            else:
                result['local']=w.publish(owner,token,name,'record_type: transport_notice\ntransport_scope: local\ntransport_kind: git_sync\nreview_verdict: null\n\nLocal Git synchronization stopped; handle only this local transport gate, not a product candidate. Never export this notice or its local response. If queue requires a bound local response, name it reviews/git-transport-response-<Queue-Event-ID>.md (or deliveries/ for build), mark transport_scope: local, retain the queue binding lines, then acknowledge only this notice.\n'+json.dumps(detail,ensure_ascii=False))
        except (HandoffError,OSError,ValueError) as exc:
            result['local_error']=str(exc)
            result.setdefault('local_errors',[]).append(str(exc))
        finally:
            if token is not None: w.release(owner,token)
        if 'desktop' not in result:
            result['desktop']=(desktop_notice('ForgeDuet Git 交接需核对：'+str(error)[:120]) if self.c['desktop_notifications'] else {'status':'disabled'})
        atomic_json(path,result)
        return result

    def retry_state(self):
        path=self.runtime/'network-retry.json'
        require(not path.is_symlink(),'Symlink network retry state')
        if not path.exists():
            value={'schema':1,'identity':self.identity,'consecutive_errors':0,'next_retry_at':None,
                   'stopped':False,'history':[],'incident':0}
            atomic_json(path,value)
            return value
        value=json.loads(path.read_text())
        require(value.get('schema')==1 and value.get('identity')==self.identity and
                type(value.get('consecutive_errors')) is int and value['consecutive_errors']>=0 and
                type(value.get('stopped')) is bool and isinstance(value.get('history'),list),
                'Corrupt network retry state; preserve and reconcile')
        value.setdefault('incident',0)
        require(type(value['incident']) is int and value['incident']>=0,'Invalid network incident counter')
        for field in ('next_retry_at','last_error_at'):
            number=value.get(field)
            require(number is None or (type(number) in (int,float) and math.isfinite(number) and number>0),
                    'Invalid retry clock')
        return value

    def resume(self):
        # Explicit operator action; does not change the Git journal or any input ack.
        with self.guard():
            self.load();retry=self.retry_state()
            retry.update(consecutive_errors=0,next_retry_at=None,stopped=False)
            retry.pop('last_error_at',None);retry.pop('stop_reason',None)
            atomic_json(self.runtime/'network-retry.json',retry)
            return {'status':'resumed','model_calls':0}

    def sync(self):
        with self.guard():
            state=self.load()
            retry=self.retry_state();now=time.time()
            require(not retry['stopped'],retry.get('stop_reason') or 'Network retries exhausted; explicit resume required after checking the cause')
            require(now+5>=retry.get('last_error_at',0),'Clock moved backwards; reconcile network retry state')
            if retry['next_retry_at'] is not None and now<retry['next_retry_at']:
                return {'status':'retrying','consecutive_errors':retry['consecutive_errors'],
                        'next_retry_at':retry['next_retry_at'],'model_calls':0}
            try:
                result={'published':self.publish(state),'received':self.receive(state),'model_calls':0}
            except RetryableGitError as exc:
                count=retry['consecutive_errors']+1
                if count==1:retry['incident']+=1
                delay=max(self.c['interval'],min(self.c['interval']*2**min(count-1,20),self.c['retry_max_seconds']))
                at=time.time()
                retry.update(consecutive_errors=count,last_error_at=at,next_retry_at=at+delay,
                             stopped=count>=self.c['max_network_errors'])
                retry['history'].append({'error':str(exc),'at':at,'next_retry_at':at+delay})
                if retry['stopped']:
                    retry['stop_reason']='Consecutive network failures reached the configured limit; inspect and resume. '+str(exc)
                atomic_json(self.runtime/'network-retry.json',retry)
                if retry['stopped']:
                    raise HandoffError(retry['stop_reason']) from exc
                return {'status':'retrying','error':str(exc),'consecutive_errors':count,
                        'next_retry_at':at+delay,'model_calls':0}
            retry.update(consecutive_errors=0,next_retry_at=None,stopped=False)
            retry.pop('last_error_at',None);retry.pop('stop_reason',None)
            atomic_json(self.runtime/'network-retry.json',retry)
            return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=('once','watch','resume'));p.add_argument('--config',required=True)
    args=p.parse_args()
    transport=None
    try:
        transport=GitTransport(args.config)
        if args.command=='resume':
            print(json.dumps(transport.resume()),flush=True)
            return 0
        while True:
            print(json.dumps(transport.sync(),ensure_ascii=False),flush=True)
            if args.command=='once':return 0
            time.sleep(transport.c['interval'])
    except (HandoffError,OSError,ValueError,subprocess.SubprocessError) as e:
        print(json.dumps({'status':'needs_human','error':str(e),'model_calls':0}),file=__import__('sys').stderr)
        if transport is not None:
            try: print(json.dumps({'notification':transport.notify(e)},ensure_ascii=False),file=__import__('sys').stderr)
            except Exception as other: print('Git stop notification also failed: '+str(other),file=__import__('sys').stderr)
        return 2
    except KeyboardInterrupt:return 130


if __name__=='__main__':raise SystemExit(main())
