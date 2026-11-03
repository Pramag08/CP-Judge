# B02 completion and current status reconciliation

2026-10-29: **B02 COMPLETE — PASS**, independently reviewed; no B02 acceptance
blocker. This follow-up inspects saved execution evidence and current status;
it does not rerun task/event/browser/restart tests or establish successful judging.

| Original requirement | Inspected acceptance evidence in `../b02-services-1/` |
| --- | --- |
| Identify native services/source | README.md, review.json, source/configuration hashes |
| Configure/start using existing locked stack | commands.json, real native service logs; existing DB/Redis reused |
| Actual connectivity | result-20261028T205851761900Z.json: Celery ping and native bridge reply |
| Harmless background task | Same result: native demo.success completed through broker/worker/results |
| Safe real event delivery | Same result: exact payload and ID through WS and HTTP poll |
| Bridge without worker enrollment | Same result: native missing-ID abort reply, listener TCP, zero judges |
| Safe lifecycle/duplicate prevention | review.json and restart/idempotent-start evidence |
| Restart and website/login smoke | commands.json, browser-20261028T205858690494Z.json; zero page errors |
| Independent review | review.json: PASS, no blockers; saved execution/source review, no reviewer runtime rerun |

[Original acceptance report](../b02-services-1/README.md) remains the authority for
executed B02 checks. Original B01/follow-up reports are historical and unchanged.
Current README, dependency selection, plan, status, AGENTS guidance and patch
inventory now agree that B02 is complete and B03 is NOT STARTED.

Current services: **all stopped**. Read-only status found website Exited (137),
MariaDB/Redis Exited (0), bridge/Celery counts zero, event daemon `false`.
The cause of the earlier website exit was not investigated in this documentation
task. No restart, password reset, provisioning, migration or database mutation
was performed. Historical successful restart acceptance remains distinct from
this observation. No judge was enrolled; B03 requires a separate explicit request.

Commands from repository root:

```sh
python3 -B deploy/site-local/manage.py start
python3 -B deploy/site-local/manage.py stop
python3 -B deploy/site-local/manage.py status
```

This follow-up ran:

- `env CPJ_SITE_REPORT_DIR=/home/pramag/Documents/CP-Judge/reports/b02-status-1 python3 -B deploy/site-local/manage.py status`: sandbox attempt exit 1 (`sg: setgid() failed`); approved external-sandbox retry exit 0. [Command ledger](commands.json), [B02 status](logs/20261029T080703121558Z/b02-status.log), [site/DB/Redis status](logs/20261029T080703121558Z/services-status.log).
- `python3 -B reports/b02-status-1/verify.py`: exit 0; [audit result](audit.json). Checks original reviewer hashes, preserved original command-ledger prefix and required saved acceptance results. The status helper appended one successful event-status inspection to the original ledger; historical entries remain exact.
- `git diff --check`: exit 0. No commit/push.

Limits retained: browser cross-origin HTTP polling fallback and durable event
replay unverified; production warnings retained; bridge startup refuses enrolled
judges/in-progress jobs because upstream resets their state. B03 must review that
guard. Worker enrollment, website judging, imports, standings and custom homepage
remain untested/unstarted. Next task: B03 only when requested.
