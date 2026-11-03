"""C11 exact immutable-data gate at native bridge selection AND final packet send.

A fresh signed worker-side byte verification is required for each dispatch. No
native wire fields are added. Denial means QU, never a contestant result.
"""
import hashlib
import json
import logging
from pathlib import Path
import secrets
import threading
import time

from django import db
from judge.models import Judge, LanguageLimit, Problem, ProblemData, Submission
from . import readiness_wire as wire

logger = logging.getLogger('judge.bridge')
CONFIG = Path('/app/cpj-readiness.json')
WAITING = ('Waiting for verified problem data and runtime on a judge. '
           'Organizers: verify the immutable installation and readiness service; '
           'this queued submission will retry automatically.')


class ReadinessPending(Exception):
    pass


def requirements(code, language):
    """Resolve frozen native identity on every check, including queued rejudges."""
    config = json.loads(CONFIG.read_text())
    if config['schema'] != 1:
        raise ReadinessPending()
    problem = Problem.objects.get(code=code)
    if code in config['legacy']:
        receipt = config['legacy'][code]
        manifest = receipt['manifest']
        if wire.digest(manifest) != receipt['manifest_digest'] or manifest['native_code'] != code:
            raise ReadinessPending()
        fields = manifest['site_values']
        allowed = fields['allowed_languages']
        checker = receipt['checker']
        digest = receipt['manifest_digest']
    else:
        from .models import ProblemVersion
        version = ProblemVersion.objects.get(code=code, problem=problem, state='published')
        manifest = version.manifest
        if wire.digest(manifest) != version.digest or manifest['code'] != code:
            raise ReadinessPending()
        fields = manifest['fields']
        from .admission import native_languages
        allowed = native_languages(version)
        checker = manifest['checker']['args']['lang']
        digest = version.digest
    # C10 languages stay disabled until C13. Readiness does not publish, assign,
    # authorize a probe or enable participant admission.
    from .models import ProbeSolution
    probe_runtime = code not in config['legacy'] and ProbeSolution.objects.filter(version=version,runtime__key=language).exists()
    if (language not in allowed and not probe_runtime) or sorted(allowed) != list(problem.allowed_languages.order_by('key').values_list('key', flat=True)):
        raise ReadinessPending()
    for field in ('time_limit', 'memory_limit', 'short_circuit', 'points', 'partial', 'is_manually_managed'):
        if getattr(problem, field) != fields[field]:
            raise ReadinessPending()
    if LanguageLimit.objects.filter(problem=problem).exists() or ProblemData.objects.filter(problem=problem).exists():
        raise ReadinessPending()
    return config, {'code': code, 'manifest_digest': digest, 'files': manifest['files'],
                    'required': sorted({language, checker})}, fields


def ready(handler, code, language):
    """Return frozen requirement or fail closed. Positive receipts are never reused."""
    try:
        if not getattr(handler, '_cpj_connection', None) or handler._stop_ping.is_set():
            raise ReadinessPending()
        config, requirement, fields = requirements(code, language)
        judge = Judge.objects.get(name=handler.name)
        if (judge.is_blocked or judge.is_disabled or not judge.online or handler.is_disabled or
                handler.name != config['worker_name'] or
                hashlib.sha256(judge.auth_key.encode()).hexdigest() != handler._cpj_auth_digest):
            raise ReadinessPending()
        for key in requirement['required']:
            expected = config['inventory']['runtime'][key]['versions']
            if json.loads(json.dumps(handler.executors.get(key))) != expected:
                raise ReadinessPending()
        if code not in handler.problems:
            raise ReadinessPending()
        connection = handler._cpj_connection
        body = {'schema': 1, **requirement, 'inventory': config['inventory'],
                'connection': connection, 'peer_port': handler.client_address[1],
                'nonce': secrets.token_hex(32), 'issued': time.time()}
        reply = wire.request(body, judge.auth_key)
        if (reply != {'schema': 1, 'request_digest': wire.digest(body), 'ok': True,
                     'connection': connection, 'nonce': body['nonce'],
                     'manifest_digest': requirement['manifest_digest']} or
                handler._cpj_connection != connection or handler._stop_ping.is_set()):
            raise ReadinessPending()
        receipt = {'connection': connection, 'code': code, 'manifest_digest': requirement['manifest_digest']}
        if getattr(handler, '_cpj_last_receipt', None) != receipt:
            logger.info('C11 verified worker=%s connection=%s code=%s manifest=%s',
                        handler.name, connection, code, requirement['manifest_digest'])
        handler._cpj_last_receipt = receipt
        return fields
    except Exception:
        # No filesystem names, hashes, runtime detail or auth secrets in public
        # status. Detailed operator diagnostics use the private verification tool.
        handler._cpj_last_receipt = None
        raise ReadinessPending() from None


def pending(submission_id):
    Submission.objects.filter(pk=submission_id, status='QU', result__isnull=True).exclude(error=WAITING).update(error=WAITING)


def validate_packet(handler, packet):
    fields = ready(handler, packet['problem-id'], packet['language'])
    if packet['problem-id'].startswith('pv9'):
        from .models import ProblemProbe
        from .probes import binding
        try:
            probe=ProblemProbe.objects.select_related('version__job','version__problem','solution__runtime','execution__source','execution__language','execution__user','owner').filter(execution_id=packet['submission-id']).first()
            if probe:
                binding(probe,dispatch=True)
                digest=probe.solution_digest
            else:
                from .admission import validate_execution
                execution=Submission.objects.get(pk=packet['submission-id'])
                validate_execution(execution)
                digest=hashlib.sha256(execution.source.source.encode()).hexdigest()
            if hashlib.sha256(packet['source'].encode()).hexdigest()!=digest:raise ReadinessPending()
        except Exception:raise ReadinessPending() from None
    sub = Submission.objects.select_related('problem', 'language').get(pk=packet['submission-id'])
    if (sub.problem.code != packet['problem-id'] or sub.language.key != packet['language'] or
            packet['time-limit'] != fields['time_limit'] or packet['memory-limit'] != fields['memory_limit'] or
            packet['short-circuit'] != fields['short_circuit']):
        raise ReadinessPending()


def install():
    """Called only by the bridge overlay after JudgeHandler is defined."""
    from judge.bridge.judge_handler import JudgeHandler
    from judge.bridge.judge_list import JudgeList
    if getattr(JudgeHandler, '_cpj_readiness_installed', False):
        return
    JudgeHandler._cpj_readiness_installed = True
    authenticate = JudgeHandler._authenticate
    connected = JudgeHandler._connected
    disconnected = JudgeHandler.on_disconnect
    can_judge = JudgeHandler.can_judge
    submit = JudgeHandler.submit
    send = JudgeHandler.send
    supported = JudgeHandler.on_supported_problems
    init_list = JudgeList.__init__
    schedule = JudgeList.judge

    def auth(self, name, key):
        self._cpj_connection = None
        self._cpj_last_receipt = None
        success = authenticate(self, name, key)
        if success:
            self._cpj_auth_digest = hashlib.sha256(key.encode()).hexdigest()
        return success

    def connect(self):
        connected(self)
        self._cpj_connection = secrets.token_hex(32)
        logger.info('C11 connection worker=%s generation=%s', self.name, self._cpj_connection)
        self.judges.update_problems(self)

    def disconnect(self):
        self._cpj_connection = None
        self._cpj_last_receipt = None
        return disconnected(self)

    def update(self, packet):
        # An advertisement update cannot extend an old receipt's lifetime.
        self._cpj_last_receipt = None
        return supported(self, packet)

    def eligible(self, problem, executor, judge_id=None):
        if not can_judge(self, problem, executor, judge_id):
            return False
        try:
            ready(self, problem, executor)
            return True
        except ReadinessPending:
            return False

    def guarded_send(self, packet):
        if packet.get('name') == 'submission-request':
            validate_packet(self, packet)
            # Clear before bytes leave: acknowledgement/compilation can race the
            # return from native send. Never present this marker as a warning.
            Submission.objects.filter(pk=packet['submission-id'], status='QU', error=WAITING).update(error=None)
        result=send(self, packet)
        if packet.get('name')=='submission-request' and packet['problem-id'].startswith('pv9'):
            from .models import ProblemProbe
            from .probes import expire
            from django.utils import timezone
            probe=ProblemProbe.objects.filter(execution_id=packet['submission-id']).first()
            if probe is None:return result
            def deadline():
                try: expire(probe.pk)
                finally: db.connections.close_all()
            timer=threading.Timer(max(0.01,(probe.expires-timezone.now()).total_seconds()),deadline)
            timer.daemon=True;timer.start()
        return result

    def dispatch(self, id, problem, language, source):
        try:
            result = submit(self, id, problem, language, source)
            return result
        except ReadinessPending:
            self._working = False
            if self._no_response_job is not None:
                self._no_response_job.cancel()
                self._no_response_job = None
            pending(id)
            return False  # patched native scheduler retains/requeues the item

    def judge(self, id, problem, language, source, judge_id, priority):
        result = schedule(self, id, problem, language, source, judge_id, priority)
        if id in self.node_map:
            pending(id)
        return result

    def init(self):
        init_list(self)
        from .contest_readiness import serve
        serve(self)
        def retry():
            while True:
                time.sleep(2)
                try:
                    with self.lock:
                        if not self.node_map:
                            continue
                        # Native current tier, target, disable and priority rules
                        # remain; all paths still invoke the guarded can_judge.
                        for worker in self.current_tier_judges():
                            if not worker.working:
                                self._handle_free_judge(worker)
                except Exception:
                    logger.exception('Readiness queue retry failed; keeping queued submissions')
                finally:
                    db.connections.close_all()
        threading.Thread(target=retry, name='cpjudge-readiness-retry', daemon=True).start()

    JudgeHandler._authenticate = auth
    JudgeHandler._connected = connect
    JudgeHandler.on_disconnect = disconnect
    JudgeHandler.on_supported_problems = update
    JudgeHandler.can_judge = eligible
    JudgeHandler.send = guarded_send
    JudgeHandler.submit = dispatch
    JudgeList.__init__ = init
    JudgeList.judge = judge
