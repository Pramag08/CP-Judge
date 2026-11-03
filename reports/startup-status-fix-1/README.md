# Local startup/status repair — 2026-11-02

**PASS.** `manage.py start` and `manage.py status` both exit 0 with the preserved local containers and database volume. The prior `b03-status` failure was the anonymous website `/status/` probe: the current `NativePolicyMiddleware` intentionally returns 401. The preceding worker container and native ORM state checks exited 0. This was a stale health check, not a worker failure or startup timing issue.

`deploy/site-local/b03.py` now uses the native judge record for online/executor state, confirms the public login page responds 200, and expects 401 from the anonymous status page. The scoped access policy remains intact. No account, password, volume, imported problem, key, or sandbox configuration was changed; no reset, migration, rejudge, commit, or push was performed.

## Checks

| Command/check | Exit | Observed result |
| --- | ---: | --- |
| `python3 -B deploy/site-local/manage.py start` | 0 | Website reported `http://127.0.0.1:8000`; B02 and B03 starts exited 0. |
| `python3 -B deploy/site-local/manage.py status` | 0 | B03/B02 status checks exited 0; site, Redis, DB running. Latest B03 state: online, CPP11/14/17/20/23, login 200, anonymous status 401. |
| Pinned Chromium container with `build/startup-status-fix-1/browser_check.py` and existing ignored import-capacity fixture | 0 | Email/password login succeeded; one labelled participant submission35 displayed AC through case103. First attempt without the host UID exited 1 on private fixture file permissions and created no submission. |
| Read-only `docker exec cpjudge-b01-site python manage.py shell -c ...` for submission35 and judge | 0 | Label in source; stored final AC, CPP23, exact `pv900000000000000003`, 103 stored AC cases each 1/1; connected worker advertises exact version and CPP23. An earlier assertion exited 1 because it expected integer case flags instead of stored `AC` strings; the corrected query exited 0. |
| `git diff --check` | 0 | No whitespace errors. |
| `python3 -B -m py_compile deploy/site-local/b03.py` | 0 | Health-check source compiles. |

The browser command was:

```sh
sg docker -c 'docker run --rm --user 1000:1000 --network host --shm-size 256m --cap-drop ALL --security-opt no-new-privileges --mount type=bind,src=/home/pramag/Documents/CP-Judge/build/import-capacity-1,dst=/run,readonly --mount type=bind,src=/home/pramag/Documents/CP-Judge/build/startup-status-fix-1,dst=/results --mount type=bind,src=/home/pramag/Documents/CP-Judge/build/startup-status-fix-1/browser_check.py,dst=/tests/browser_check.py,readonly cpjudge-b01-browser:local1 python /tests/browser_check.py'
```

The passing read-only ORM command was:

```sh
sg docker -c 'docker exec cpjudge-b01-site python manage.py shell -c "from judge.models import Submission,Judge; s=Submission.objects.select_related(\"source\",\"judged_on\",\"language\",\"problem\").get(pk=35); j=Judge.objects.get(name=\"cpjudge-local-worker\"); cases=list(s.test_cases.values_list(\"status\",\"points\",\"total\")); assert s.source.source.startswith(\"// STARTUP STATUS RECOVERY TEST 2026-11-02\"); assert s.status==\"D\" and s.result==\"AC\" and s.language.key==\"CPP23\" and s.problem.code==\"pv900000000000000003\" and s.judged_on_id==j.pk; assert len(cases)==103 and all(status==\"AC\" and points==total==1 for status,points,total in cases); assert j.online and j.problems.filter(pk=s.problem_id).exists() and j.runtimes.filter(key=\"CPP23\").exists(); print(\"PASS: labelled submission 35 stored AC, 103/103 native cases; connected CPP23 worker advertises exact problem\")"'
```

Raw original failure log: `build/b01-site-1/logs/20261102T150022433026Z/b03-status.log`; private browser receipt/result and script: `build/startup-status-fix-1/`. Sanitized worker state: latest `reports/b03-worker-1/state-*.json`. The bounded browser check added exactly one test submission and no fixture or account reset. The contest and problem were already present. This check does not test startup from a fully stopped state or in-flight job recovery. Next task: return to the previously selected MVP task only on request.
