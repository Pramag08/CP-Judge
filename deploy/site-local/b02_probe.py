import json,socket,struct,zlib,time,uuid,urllib.request
from websocket import create_connection
from django.conf import settings
from django.contrib.auth.models import User
from judge.models import Judge,Submission
from judge import event_poster
from dmoj_celery import app
assert not Judge.objects.exists()
assert not Submission.objects.filter(status__in=Submission.IN_PROGRESS_GRADING_STATUS).exists()
assert event_poster.real
reply=app.control.ping(timeout=5);assert reply,reply
job=app.send_task('judge.tasks.demo.success');assert job.get(timeout=30) is None and job.successful()
channel='b02-diagnostic-'+uuid.uuid4().hex
receiver=create_connection('ws://events:9996/',timeout=10)
receiver.send(json.dumps({'command':'start-msg','start':0}))
receiver.send(json.dumps({'command':'set-filter','filter':[channel]}));time.sleep(.2)
message={'kind':'b02-service-diagnostic','nonce':uuid.uuid4().hex}
mid=event_poster.post(channel,message);assert mid>0
received=json.loads(receiver.recv());assert received['id']==mid and received['message']==message and received['channel']==channel
receiver.close()
with urllib.request.urlopen('http://events:9995/channels/'+channel+'?last=0',timeout=5) as response:
 assert json.load(response)==received
packet=zlib.compress(json.dumps({'name':'terminate-submission','submission-id':-1}).encode())
s=socket.create_connection(settings.BRIDGED_DJANGO_CONNECT,5);s.sendall(struct.pack('!I',len(packet))+packet)
def exact(n):
 data=b''
 while len(data)<n:
  part=s.recv(n-len(data));assert part;data+=part
 return data
size=struct.unpack('!I',exact(4))[0];answer=json.loads(zlib.decompress(exact(size)));s.close()
assert answer=={'name':'submission-received','judge-aborted':False},answer
# TCP listener only; no judge handshake or enrollment.
s=socket.create_connection(('127.0.0.1',9999),5);s.close()
print(json.dumps({'status':'PASS','celery_ping':True,'native_noop_task_completed':True,'websocket_event_exact_delivery':True,
'http_poll_exact_delivery':True,'bridge_native_missing_abort_response':answer,'judge_listener_tcp':True,'judges':Judge.objects.count(),
'judging':'NOT TESTED','browser_poll_cors':'NOT TESTED; native daemon has no cross-origin CORS headers'},indent=2))
