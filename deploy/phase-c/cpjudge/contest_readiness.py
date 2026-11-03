"""Fresh authenticated bridge challenge; no DMOJ protocol extensions."""
import json, secrets, time
from . import readiness_wire as wire
from .bridge_readiness import CONFIG

def check(code,language):
    from judge.models import Judge
    config=json.loads(CONFIG.read_text())
    worker=Judge.objects.get(name=config['worker_name'],online=True,is_blocked=False,is_disabled=False)
    body={'schema':1,'code':code,'language':language,'nonce':secrets.token_hex(32),'issued':time.time()}
    reply=wire.request(body,worker.auth_key,address=('127.0.0.1',9995))
    if reply!={'schema':1,'ok':True,'request_digest':wire.digest(body)}:raise ValueError('Worker readiness unavailable')


def serve(judges):
    import socketserver, threading
    from judge.models import Judge
    from django import db
    from .bridge_readiness import ready
    class Handler(socketserver.BaseRequestHandler):
        def handle(self):
            try:
                self.request.settimeout(12)
                config=json.loads(CONFIG.read_text())
                worker=Judge.objects.get(name=config['worker_name'])
                body=wire.unseal(wire.read_frame(self.request),worker.auth_key)
                if (set(body)!={'schema','code','language','nonce','issued'} or body['schema']!=1 or
                    abs(time.time()-body['issued'])>15 or len(body['nonce'])!=64):raise ValueError()
                with judges.lock:
                    handler=next(h for h in judges.judges if h.name==worker.name)
                    ready(handler,body['code'],body['language'])
                wire.write_frame(self.request,wire.seal({'schema':1,'ok':True,'request_digest':wire.digest(body)},worker.auth_key))
            except Exception:
                import logging
                logging.getLogger('judge.bridge').exception('Contest publication readiness denied')
            finally:db.connections.close_all()
    class Server(socketserver.ThreadingTCPServer):
        allow_reuse_address=True
        daemon_threads=True
    server=Server(('127.0.0.1',9995),Handler)
    threading.Thread(target=server.serve_forever,name='contest-publication-readiness',daemon=True).start()
