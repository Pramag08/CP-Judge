"""Small reproducible native scheduler overlay; upstream attribution preserved."""
from pathlib import Path

root = Path('/app')
p = root/'judge/bridge/judge_handler.py'
s = p.read_text()
line = '\n# C11: private manifest readiness, no native protocol fields.\nfrom cpjudge.bridge_readiness import install as _c11_install\n_c11_install()\n'
if line not in s:
    s += line
# Retain the historical observer log; new native packets get a fresh private log.
s=s.replace("'/tmp/b07-native-trace.jsonl'", "'/tmp/c11-native-trace.jsonl'")
compile(s, str(p), 'exec');p.write_text(s)
p = root/'judge/bridge/judge_list.py';s=p.read_text()
old = '                            judge.submit(id, problem, language, source)'
new = '''                            # C11: no packet was sent; preserve the queue node.
                            if judge.submit(id, problem, language, source) is False:
                                self.submission_map.pop(id, None)
                                return'''
if new not in s:
    assert s.count(old)==1;s=s.replace(old,new)
old = '                    judge.submit(id, problem, language, source)'
new = '''                    # C11: final-send readiness may change after selection.
                    if judge.submit(id, problem, language, source) is False:
                        self.submission_map.pop(id, None)
                        self.node_map[id] = self.queue.insert(
                            (id, problem, language, source, judge_id), self.priority[priority])
                        return'''
if new not in s:
    assert s.count(old)==1;s=s.replace(old,new)
compile(s,str(p),'exec');p.write_text(s)
p=root/'templates/submission/status-testcases.html';s=p.read_text()
old="{{ _('We are waiting for a suitable judge to process your submission...') }}"
new="{{ submission.error if submission.error and submission.error.startswith('Waiting for verified problem data') else _('We are waiting for a suitable judge to process your submission...') }}"
if new not in s:
    assert s.count(old)==1;s=s.replace(old,new)
p.write_text(s)
print('C11 native selection/final-send/pending-status overlay installed; native packet schema unchanged.')
