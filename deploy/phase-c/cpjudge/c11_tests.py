"""C11 isolated MariaDB/native bridge tests; worker I/O uses immutable temp data.

These are not actual problem judging. The one live submission is separate.
"""
import hashlib
import json
import os
from pathlib import Path
import secrets
import socket
import struct
import sys
import tempfile
import threading
import time
from types import SimpleNamespace
from unittest.mock import Mock, patch
import zlib

from django.contrib.auth import get_user_model
from django.test import TestCase, SimpleTestCase
from judge.models import Judge, Language, LanguageLimit, Problem, ProblemGroup, Profile, Submission, SubmissionSource
from judge.bridge.judge_handler import JudgeHandler
from judge.bridge.judge_list import JudgeList
from cpjudge import bridge_readiness as gate, readiness_wire as wire, c11_worker as worker
from cpjudge.models import ProblemVersion, ImportJob


class DispatchTests(TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.code='pv000000000000000099'
        self.folder=self.root/self.code;self.folder.mkdir()
        for name in ('init.yml','data.zip','checker.cpp'):(self.folder/name).write_bytes(name.encode())
        self.freeze()
        self.files=worker.installed_files(self.code,self.root)
        self.language=Language.objects.create(key='CPP23',name='C++23',short_name='C++23',common_name='C++',extension='cpp',ace='c_cpp',pygments='cpp')
        self.user=get_user_model().objects.create_user('c11test')
        Profile.objects.get_or_create(user=self.user)
        group=ProblemGroup.objects.create(name='C11',full_name='C11')
        self.problem=Problem.objects.create(code=self.code,name='Private C11 fixture',group=group,time_limit=2,memory_limit=262144,
            short_circuit=False,points=3,partial=True,is_manually_managed=True)
        self.problem.allowed_languages.add(self.language)
        self.fields={k:getattr(self.problem,k) for k in ('time_limit','memory_limit','short_circuit','points','partial','is_manually_managed')}
        self.fields['allowed_languages']=['CPP23']
        self.manifest={'native_code':self.code,'files':self.files,'site_values':self.fields}
        self.inventory={'runtime':{'CPP23':{'versions':[['g++',[16]]]},'CPP17':{'versions':[['g++',[16]]]}},'source_pin':'pinned'}
        self.config={'schema':1,'worker_name':'c11worker','inventory':self.inventory,
            'legacy':{self.code:{'manifest':self.manifest,'manifest_digest':wire.digest(self.manifest),'checker':'CPP17'}}}
        self.config_path=self.root/'enrollment.json';self.write_config()
        self.addCleanup(patch.stopall)
        patch('judge.bridge.judge_handler._ensure_connection').start()
        patch('judge.bridge.judge_handler._b07_observe').start()
        patch.object(gate,'CONFIG',self.config_path).start()
        self.runtime=patch.object(worker,'inventory',return_value=self.inventory).start()
        self.connection=patch.object(worker,'owns_native_connection',return_value=True).start()
        original_files=worker.installed_files
        self.bytecheck=patch.object(worker,'installed_files',side_effect=lambda code:original_files(code,self.root)).start()
        self.requests=[]
        def exchange(body,key):
            self.requests.append(body)
            # Exercise actual service validation and HMAC helpers. No socket/worker
            # is simulated as an actual executor or counted as judging evidence.
            decoded=wire.unseal(wire.seal(body,key),key)
            return wire.unseal(wire.seal(worker.verify(decoded,None,self.inventory),key),key)
        self.exchange=patch.object(wire,'request',side_effect=exchange).start()
        self.judge=Judge.objects.create(name='c11worker',auth_key=secrets.token_hex(32),online=True,tier=0)
        with patch.object(threading.Thread,'start'):
            self.judges=JudgeList()
        self.handler=self.new_handler()
        self.judges.judges.add(self.handler);self.judges._update_min_tier()
        self.sub=Submission.objects.create(user=self.user.profile,problem=self.problem,language=self.language)
        SubmissionSource.objects.create(submission=self.sub,source='int main(){}')

    def freeze(self):
        for path in self.folder.iterdir():path.chmod(0o444)
        self.folder.chmod(0o555)

    def write_config(self):self.config_path.write_text(json.dumps(self.config))

    def new_handler(self):
        obj=object.__new__(JudgeHandler)
        JudgeHandler.__init__(obj,Mock(),('127.0.0.1',43210),SimpleNamespace(server_address=('127.0.0.1',9999)),self.judges)
        obj.judge=self.judge;obj.name=self.judge.name;obj.tier=0;obj.load=0
        obj.problems={self.code:1};obj.executors={k:r['versions'] for k,r in self.inventory['runtime'].items()}
        obj._cpj_connection=secrets.token_hex(32)
        obj._cpj_auth_digest=hashlib.sha256(self.judge.auth_key.encode()).hexdigest()
        return obj

    def enqueue(self,target=None):self.judges.judge(self.sub.pk,self.code,'CPP23','int main(){}',target,0)

    def packet(self):
        data=self.handler.request.sendall.call_args.args[0]
        return json.loads(zlib.decompress(data[4:]))

    def assert_pending(self):
        self.sub.refresh_from_db()
        self.assertEqual(self.sub.status,'QU');self.assertIsNone(self.sub.result)
        self.assertEqual(self.sub.error,gate.WAITING)
        self.assertIn(self.sub.pk,self.judges.node_map)
        self.assertNotIn(self.sub.pk,self.judges.submission_map)
        self.handler.request.sendall.assert_not_called()
        self.assertFalse(self.sub.test_cases.exists())

    def test_matching_data_runtime_dispatch_native_packet(self):
        self.enqueue()
        self.assertEqual(self.packet()['problem-id'],self.code)
        self.assertEqual(self.packet()['time-limit'],2)
        self.assertEqual(self.packet()['memory-limit'],262144)
        self.assertEqual(self.packet()['language'],'CPP23')
        self.assertNotIn('hash',self.packet());self.assertNotIn('version',self.packet())
        self.assertEqual(len(self.requests),2)  # selection + final send
        self.assertNotIn(self.sub.pk,self.judges.node_map)

    def test_advertised_but_missing_version_blocks(self):
        self.folder.chmod(0o755)
        for path in self.folder.iterdir():path.unlink()
        self.folder.rmdir()
        self.enqueue();self.assert_pending()

    def test_same_size_and_mtime_corruption_blocks(self):
        path=self.folder/'data.zip';st=path.stat();path.chmod(0o644)
        path.write_bytes(b'x'*st.st_size);os.utime(path,ns=(st.st_atime_ns,st.st_mtime_ns));path.chmod(0o444)
        self.enqueue();self.assert_pending()

    def test_extra_file_or_symlink_blocks(self):
        self.folder.chmod(0o755)
        (self.folder/'extra').symlink_to(self.folder/'data.zip')
        self.folder.chmod(0o555)
        self.enqueue();self.assert_pending()

    def test_wrong_manifest_digest_blocks(self):
        self.config['legacy'][self.code]['manifest_digest']='0'*64;self.write_config()
        self.enqueue();self.assert_pending()

    def test_changed_manifest_invalidates_previously_valid_receipt(self):
        self.assertTrue(self.handler.can_judge(self.code,'CPP23'))
        self.assertIsNotNone(self.handler._cpj_last_receipt)
        receipt=self.config['legacy'][self.code]
        receipt['manifest']['files'][0]['sha256']='0'*64
        receipt['manifest_digest']=wire.digest(receipt['manifest']);self.write_config()
        self.enqueue();self.assert_pending();self.assertIsNone(self.handler._cpj_last_receipt)

    def test_supported_problem_update_cannot_reuse_receipt(self):
        self.assertTrue(self.handler.can_judge(self.code,'CPP23'))
        self.handler.on_supported_problems({'problems':[[self.code,2]]})
        self.assertIsNone(self.handler._cpj_last_receipt)
        self.exchange.side_effect=OSError('Fresh verifier unavailable')
        self.enqueue();self.assert_pending()

    def test_checker_executor_required_even_if_solution_advertised(self):
        del self.handler.executors['CPP17'];self.enqueue();self.assert_pending()

    def test_wrong_executor_version_blocks(self):
        self.handler.executors['CPP23']=[['g++',[15]]];self.enqueue();self.assert_pending()

    def test_runtime_inventory_change_blocks(self):
        self.runtime.return_value={'runtime':{}};self.enqueue();self.assert_pending()

    def test_explicit_target_cannot_bypass_disabled_or_revoked_worker(self):
        self.judge.is_blocked=True;self.judge.save(update_fields=['is_blocked'])
        self.enqueue(self.judge.name);self.assert_pending()
        self.judge.is_blocked=False;self.judge.is_disabled=True;self.judge.save()
        self.judges._handle_free_judge(self.handler);self.assert_pending()

    def test_key_rotation_invalidates_existing_connection(self):
        self.judge.auth_key=secrets.token_hex(32);self.judge.save()
        self.enqueue();self.assert_pending()

    def test_changed_native_limits_or_language_override_blocks(self):
        LanguageLimit.objects.create(problem=self.problem,language=self.language,time_limit=4,memory_limit=262144)
        self.enqueue();self.assert_pending()

    def test_stale_response_cannot_be_replayed(self):
        self.enqueue();reply=worker.verify(self.requests[-1],None,self.inventory)
        self.handler._working=False;self.handler.request.reset_mock();self.judges.submission_map.clear()
        self.exchange.side_effect=None;self.exchange.return_value=reply
        self.enqueue();self.assert_pending()

    def test_disconnect_reconnect_requires_new_connection_receipt(self):
        old=self.handler._cpj_connection
        self.handler.on_disconnect()
        self.assertIsNone(self.handler._cpj_connection)
        self.assertFalse(self.handler.can_judge(self.code,'CPP23'))
        self.judge.refresh_from_db();self.assertFalse(self.judge.online)
        self.judge.online=True;self.judge.save()
        self.handler=self.new_handler();self.assertNotEqual(old,self.handler._cpj_connection)
        self.judges.judges.add(self.handler);self.judges._update_min_tier()
        self.connection.return_value=False;self.enqueue();self.assert_pending()
        self.connection.return_value=True;self.judges._handle_free_judge(self.handler)
        self.assertEqual(self.packet()['submission-id'],self.sub.pk)

    def test_queue_resumes_after_missing_data_restored(self):
        original=(self.folder/'data.zip').read_bytes();path=self.folder/'data.zip';path.chmod(0o644);path.write_bytes(b'corrupt');path.chmod(0o444)
        self.enqueue();self.assert_pending()
        path.chmod(0o644);path.write_bytes(original);path.chmod(0o444)
        self.judges._handle_free_judge(self.handler)
        self.assertEqual(self.packet()['submission-id'],self.sub.pk)
        self.assertNotIn(self.sub.pk,self.judges.node_map)
        self.assertIn(self.sub.pk,self.judges.submission_map)

    def test_pending_message_is_cleared_before_acknowledgement_race(self):
        exchange=self.exchange.side_effect
        self.exchange.side_effect=OSError('service unavailable');self.enqueue();self.assert_pending()
        self.exchange.side_effect=exchange
        def acknowledge_immediately(data):
            self.sub.refresh_from_db();self.assertIsNone(self.sub.error)
            Submission.objects.filter(pk=self.sub.pk).update(status='P')
        self.handler.request.sendall.side_effect=acknowledge_immediately
        self.judges._handle_free_judge(self.handler)
        self.sub.refresh_from_db();self.assertEqual(self.sub.status,'P');self.assertIsNone(self.sub.error)

    def test_final_send_failure_retains_direct_submission_then_retries(self):
        original=self.exchange.side_effect
        def fail_final(body,key):
            if self.requests:raise ValueError('Readiness changed after selection')
            return original(body,key)
        self.exchange.side_effect=fail_final
        self.enqueue();self.assert_pending()
        self.exchange.side_effect=original
        self.judges._handle_free_judge(self.handler)
        self.assertEqual(self.packet()['submission-id'],self.sub.pk)

    def test_final_send_failure_keeps_queued_node_and_no_submission_map(self):
        self.exchange.side_effect=OSError('service offline');self.enqueue();self.assert_pending()
        def fail_final(body,key):
            self.requests.append(body)
            if len(self.requests)%2==0:raise ValueError('last check failed')
            return worker.verify(body,None,self.inventory)
        self.requests.clear();self.exchange.side_effect=fail_final
        self.judges._handle_free_judge(self.handler);self.assert_pending()

    def test_direct_handler_submit_cannot_bypass_gate(self):
        self.connection.return_value=False
        self.assertIs(self.handler.submit(self.sub.pk,self.code,'CPP23','int main(){}'),False)
        self.handler.request.sendall.assert_not_called();self.assertFalse(self.handler.working)

    def test_c10_unready_publication_does_not_enable_languages(self):
        code='pv900000000000000099';self.problem.code=code;self.problem.save();self.problem.allowed_languages.clear()
        job=ImportJob.objects.create(owner=self.user,package_sha256='a'*64,archive_key='fixture',status='succeeded')
        manifest={'code':code,'files':self.files,'fields':self.fields,'allowed_languages':[],
                  'checker':{'args':{'lang':'CPP17'}}}
        ProblemVersion.objects.create(job=job,attempt=1,token='fixture',code=code,state='published',manifest=manifest,digest=wire.digest(manifest),problem=self.problem)
        with self.assertRaises(gate.ReadinessPending):gate.requirements(code,'CPP23')
        self.assertFalse(self.problem.allowed_languages.exists())

    def test_final_packet_wrong_limits_or_identity_blocks(self):
        packet={'name':'submission-request','submission-id':self.sub.pk,'problem-id':self.code,'language':'CPP23',
                'time-limit':999,'memory-limit':262144,'short-circuit':False}
        with self.assertRaises(gate.ReadinessPending):self.handler.send(packet)
        self.handler.request.sendall.assert_not_called()

    def test_duplicate_admission_and_other_explicit_target_remain_queued_once(self):
        self.enqueue('another-worker');self.enqueue('another-worker');self.assert_pending()
        self.assertEqual(len(self.judges.node_map),1)


class ChannelTests(SimpleTestCase):
    def test_mac_modification_and_wrong_key_rejected(self):
        signed=wire.seal({'nonce':'x'},'key')
        with self.assertRaises(ValueError):wire.unseal(signed,'wrong')
        signed['body']['nonce']='y'
        with self.assertRaises(ValueError):wire.unseal(signed,'key')

    def test_framed_size_bound_and_roundtrip(self):
        a,b=socket.socketpair()
        try:
            wire.write_frame(a,wire.seal({'ok':True},'key'))
            self.assertEqual(wire.unseal(wire.read_frame(b),'key'),{'ok':True})
            a.sendall(struct.pack('!I',wire.MAX_FRAME+1))
            with self.assertRaises(ValueError):wire.read_frame(b)
        finally:a.close();b.close()

    def test_expired_worker_challenge_rejected(self):
        with self.assertRaises(ValueError):worker.verify({'schema':1,'nonce':'a'*64,'connection':'b'*64,'issued':time.time()-60},None,{})

    def test_native_socket_is_bound_to_supervisor_inode_and_port(self):
        with tempfile.TemporaryDirectory() as temp:
            proc=Path(temp);(proc/'1/fd').mkdir(parents=True);(proc/'net').mkdir()
            (proc/'1/cmdline').write_bytes(b'/env/bin/python3\0/env/bin/dmoj\0')
            (proc/'1/exe').symlink_to(Path(sys.executable).resolve())
            (proc/'1/fd/7').symlink_to('socket:[123]')
            (proc/'net/tcp').write_text('header\n 0: 0100007F:A8CA 0100007F:270F 01 0 0 0 0 0 123\n')
            (proc/'net/tcp6').write_text('header\n')
            self.assertTrue(worker.owns_native_connection(43210,proc))
            (proc/'1/cmdline').write_bytes(b'DMOJ Judge c11worker on 127.0.0.1:9999\0')
            self.assertTrue(worker.owns_native_connection(43210,proc))
            (proc/'1/cmdline').write_bytes(b'spoofed unrelated process\0')
            self.assertFalse(worker.owns_native_connection(43210,proc))
            (proc/'1/cmdline').write_bytes(b'DMOJ Judge c11worker on 127.0.0.1:9999\0')
            self.assertFalse(worker.owns_native_connection(43211,proc))
            (proc/'1/fd/7').unlink()
            self.assertFalse(worker.owns_native_connection(43210,proc))
