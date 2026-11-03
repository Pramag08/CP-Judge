**B12 PASS; Phase B / M1 COMPLETE — PASS for the scoped local website-to-judge proof.**
One agent; existing private contest `b10b11local1`; no application fix.

| Check | Observed result |
| --- | --- |
| Supported lifecycle | `manage.py stop` then `start`, both exit0; all five containers stopped and restarted; same IDs, images and named DB volume; no deletion/reset |
| Existing credentials | Both contest accounts plus existing staff/participant credentials authenticated in real Chromium before and after restart |
| Completed results | All11 existing submissions and927 testcase rows preserved exactly across88 model snapshots; contest, verdicts, sources and standings unchanged |
| Worker reconnect | Fresh native start time, authenticated online, installed problem and CPP11/14/17/20/23 advertised |
| New real browser submission | Submission12, participant B, CPP23:103 actual AC cases; worker log/callbacks, SQL and browser agree;2s/262144KiB unchanged |
| Standings update | New official attempt recorded; both remain1 solved/2161s/shared rank1, stable B/A order; a later AC adds no new solve or penalty |
| Preservation | Original accounts/password hashes, problem/statement bytes, limits, container/worker/sandbox configuration and earlier results preserved |

Evidence: [before](before-results.json), [after restart](after-results.json),
[credentials/browser comparison](after-acceptance.json), [new result](final-results.json),
[native trace](new-native-trace.json), [final preservation](final-preservation.json),
[acceptance](acceptance.json), [exact commands/exits/private log paths](commands.json).
Raw logs, DOM/screenshots and snapshots stay ignored under `build/b12-restart-1/`.
Only acceptance drivers were added/extended; previous milestone evidence was reused.

Commands: `.venv/bin/python -B deploy/site-local/restart_journey.py <action>` with
`snapshot`, `stop`, `start`, `after`, `submit`, `final`: each exit0. Lifecycle actions
invoke `python -B deploy/site-local/manage.py stop|start` separately. Syntax and
`git diff --check` exit0. No migrations, account reset, rejudge or volume deletion.

**Limit:** graceful restart with no in-progress work proves completed-result
persistence, not recovery of submissions interrupted during judging. No crash,
backup/restore, load or production-readiness claim. Prior Phase B evidence/limits
remain linked in PROJECT_STATUS.md; no unrelated milestones were rerun.
**Stopped before Phase C.** No UI changes, commit or push.
