# C11 — exact version readiness at native bridge dispatch

**COMPLETE — local PASS, one agent.** Existing immutable codes/manifests and
pinned native worker are reused; no DMOJ protocol fields, dependencies, schema,
credentials or sandbox settings changed. C12/C13 were not implemented or run.

`cpjudge/bridge_readiness.py` gates native selection and final packet send,
including queued/free-judge and explicit-target paths. A private loopback verifier
inside the existing worker hashes every installed file afresh and checks the
pinned source/configuration, compiler binaries and required solution **and checker**
executors. HMAC challenges bind the response to a fresh nonce and the authenticated
bridge connection; the verifier matches that connection's TCP port/socket inode
to the native PID1 supervisor/interpreter (including its native process title).
Disconnect/revocation, changed manifests/runtimes or mismatches cannot reuse a
positive receipt. No positive receipt authorizes a later dispatch without rechecking.

Denial retains native **QU**, no result/cases, with an actionable private-page
message; native queue items survive final-send denial and retry every two seconds.
The message clears before sending, avoiding an acknowledgement/compile-log race.
B03 startup idempotently starts the verifier in the existing read-only container's
writable `/tmp`; no second worker, Docker socket or externally exposed port added.

| Check | Actual result |
| --- | --- |
| Focused native tests | **27 passed, 0 skips**, isolated MariaDB/native handler/scheduler: matching bytes; missing/corrupt/same-mtime/linked data; changed manifest/advertisement; stale response; missing checker/wrong runtime; revoked/disabled/explicit target; changed limits; direct/queued final-send retention/resumption; acknowledgement race; MAC/frame/challenge bounds and native socket ownership. Worker I/O uses temporary immutable files and a mocked transport, not actual judging. |
| One real browser submission | **16, CPP23, AC103/103**, native form/bridge/worker/callback/SQL/display agree; exactly **one** submission-request,2s/262144KiB; all103 executed cases AC1/1;3 compiler warnings retained. |
| Live denial/reconnect | A deliberately mismatched private C11 expectation kept16 QU with zero cases/no packet, including offline → authenticated reconnect. Original B05 registry and installed bytes were untouched. Restoring the valid expectation and correcting the verifier allowed automatic queue resumption, without another POST or verdict writes. |
| Preservation | **64 model sets/1849 prior rows**, including15 submissions/1236 cases, original accounts/passwords/IDs/emails/audits/contest results and both C10 versions preserved. Only normal login/generation/liveness/access and problem AC-rate activity changed. Native ended-contest browser join added one spectator participation and its ContestSubmission; retained with16, original profile contest pointer restored. |
| Deployment | Same four containers/images/configuration/mounts; only the existing worker container restarted. Private problem bytes/registry/worker credentials unchanged. Migration consistency and verifier lifecycle idempotence exit0. |

[Actual result](live.json), [preservation](preservation.json),
[checks/source identities](checks.json), [runtime boundary](runtime.json),
[exact subprocess commands/exits](commands.json). Raw output, readable private DB
backup, original native files, receipts and browser screenshots remain ignored in
`build/phase-c-c11-1/`. No historical report was modified.

Commands from repository root (operator driver enters the existing Docker group):

```sh
python3 -B deploy/phase-c/c11.py backup
python3 -B deploy/phase-c/c11.py stage
python3 -B deploy/phase-c/c11.py tests
python3 -B deploy/phase-c/c11.py activate
python3 -B deploy/phase-c/c11.py live
python3 -B deploy/phase-c/c11.py refresh-verifier
python3 -B deploy/phase-c/c11.py finish
python3 -B deploy/phase-c/c11.py preserve
python3 -B deploy/phase-c/c11.py final-checks
git diff --check
```

Final backup/stage/tests/activation/refresh/finish/preservation/check commands exit0.
The initial `live` controller exited1 after its180s wait: native `setproctitle`
caused the first verifier to reject a valid supervisor. Submission16 remained QU;
only the verifier was corrected/restarted and the **original browser** completed
AC103. `finish` then validated it; its detached Docker return status was not
collected after the controller timeout. Staging copy/ownership and the first
pointer-preservation assertions also failed before correction; all attempts are
retained in the command ledger/private logs, not counted as acceptance passes.
Final focused tests cover the process-title and pending-message races. Final code
was reloaded while idle; no second real submission or historical judging rerun.

Limits: trusted single-host operator/worker attestation, not malicious-host or
hardware attestation; immutable read-only installation is still required (no
claim against privileged mutation racing a completed hash check). Full bridge/host
crash recovery, in-flight worker loss, load/capacity, multiple workers and backup
restore remain untested. The supported lifecycle guard still refuses bridge restart with queued
jobs; do not bypass that guard. C10 versions remain private and submission-disabled;
C13 restricted probes/publication readiness are **pending**. No new package or
additional language was judged. Original111MiB ZIP still exceeds unchanged
32MiB upload/128MiB conversion limits; this is not its full website import proof.

Recovery: check private `/tmp/c11-readiness.log` in the worker, frozen manifest and
runtime enrollment. With the worker online, run `sg docker -c 'python3 -B deploy/site-local/worker_readiness.py start'` if its verifier is absent; native
queue retry resumes after valid readiness returns. Never rewrite immutable bytes
or bless a new digest to clear an error. `stage` refuses changed runtime enrollment.
Do not disable the gate to drain a queue.

**Next: unfinished C12 (still partial), only on request. Stop before C12/C13.**
No commit or push.
