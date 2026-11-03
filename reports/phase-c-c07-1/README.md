# C07 — queued private conversion

**COMPLETE — local C07 acceptance PASS.** The native DMOJ upload confirmation now
has a CSRF-protected Convert/Retry action and an owner-authorized status page.
`queued`, `running`, `succeeded` and `failed`, attempt number, timestamps and safe
errors persist in the existing ImportJob. Uploading alone still does not convert.
Success means conversion only: no compatibility preview, publication or judging.

Queue admission locks the job and publishes only with `transaction.on_commit`.
Duplicate requests keep the current attempt. Celery claims a matching attempt/
random token once, rechecks current owner/import permission before and after work,
and fences completion against newer attempts. Outputs use private token-specific
directories, with an ownership manifest required for stale-attempt cleanup. The
old synchronous helper cannot modify a tokenized job.

A trusted child reuses C06 extraction and the pinned strict converter. It invokes
only trusted Python/Git dependency checks, never uploaded checkers, solutions,
generators, validators or scripts. No dependencies were installed into the web
runtime. Original ZIPs and attempt staging/output stay outside static/media under
`/app/private-cpj-imports`, private directories0700/files0600.

Bounds: Celery solo concurrency1 and prefetch1; a filesystem lock also limits all
conversion processes to one, with a5s acquisition deadline. The child inherits
that lock so it survives loss of its Celery parent. Child alarm120s, parent
wait125s then process-group kill, CPU60s, address space768MiB, individual file
size256MiB and128 open files are enforced. Extraction uses expanded128MiB and
member64MiB limits in every converter extraction pass. Import-only broker connect/
socket timeouts are3s with publish retries disabled. Aggregate retained storage
quotas and capacity/load acceptance remain future work.

## Actual acceptance

| Requirement/check | Actual result |
| --- | --- |
| Browser → actual Celery conversion | PASS: final supported job13 observed queued → running → succeeded, attempt1; two refreshes preserved terminal state. [Browser evidence](browser-supported-bounded.json). |
| Safe input failures | PASS: unsupported interactive metadata job8 and malformed XML job9 reached failed with actionable errors and no internal paths. [Unsupported](browser-unsupported.json), [malformed](browser-malformed.json). |
| Scope and CSRF | PASS: missing CSRF403; unrelated author inspection/queue404 through real HTTP; tests also cover permission revocation at execution. |
| Duplicate/concurrent attempts | PASS: actual duplicate Celery deliveries returned False and preserved the full row/output manifest; native MariaDB concurrent admission, rollback, stale completion and cleanup ownership tests passed. [Duplicate evidence](duplicates.json). |
| Queue failure | PASS: real Kombu connection refusal against an unused local port persisted safe failed attempt1; browser retry job12 succeeded as attempt2. Project Redis was not stopped or reconfigured. [Evidence](broker-failure.json). |
| Worker interruption/reconciliation | PASS: real Celery SIGKILL while task10 was running and waiting for the held global conversion lock; fixture lease advanced181s, reconciliation marked failed, browser retry succeeded as attempt2. Judge untouched. [Evidence](interruption.json). |
| Runtime/resources | PASS: actual trusted-child test observed kernel rlimits and independent alarm expiry. No package code used for this test. |
| Focused tests | Final12 passed, exit0:11 C07 checks (including concurrent race) plus actual child resource/alarm test. Earlier17-test run included8 existing C05 checks and overlapping C07 cases; these are not29 unique checks. |
| Data/configuration | PASS:63 model sets/1749 existing rows checked; only native login/access/session-generation and judge liveness changes allowed. Original passwords, college IDs, results and worker keys preserved. Container IDs/images/configuration/start times, including judge sandbox, unchanged. [Rows](preservation.json), [containers](containers-preserved.json). |

Fresh private backup preceded real additive migration0005; complete gzip readback
passed. Restore was not tested. [Migration receipt](migration.json). Only HTTP and
Celery processes were reloaded; containers, bridge and native judge were retained.
Migration generation initially failed on directory ownership; using the existing
application-directory owner fixed it. No host security setting changed.

## Recovery and reproduction

Publication exceptions mark only the matching queued attempt failed. Lost queued
delivery expires after300s; running attempts expire after180s. Visiting the owned
status page or retry action reconciles that job. Operators must run the following
after a worker/broker outage (and periodically for unattended jobs):

```sh
sg docker -c 'docker exec cpjudge-b01-site python manage.py reconcile_imports'
```

Reconciliation marks expired work failed, cleans only matching owned attempt
files when no converter holds the lock, and exposes Retry. The retry creates a
new token; delayed old deliveries/completions cannot update it. No periodic
scheduler was added: unattended recovery requires this operator command. The real
interruption test accelerated only a task-owned fixture lease, not the clock or
existing results; it interrupted the lock-wait phase, not a mid-converter host
crash. Orphan filesystem recovery after full host/process-group crashes remains
limited to the recorded attempt tree and requires operator reconciliation.

Run focused checks from the repository root:

```sh
sg docker -c 'python3 -B deploy/phase-c/c07.py tests'
sg docker -c 'python3 -B deploy/phase-c/c07_activate.py preserve'
git diff --check
```

Final commands exited0; [commands.json](commands.json) retains successful and
failed explorations, with raw output only under ignored private `build/` paths.
Browser/recovery fixtures are retained; interruption and broker-failure driver
actions refuse blind repetition. `c07.py browser supported-bounded` reviews the
completed fixture through the normal page; use a new named fixture for a new run.

Manual flow: sign in as the scoped author, open
`http://127.0.0.1:8000/contest/c1livea/import/`, upload one supported Polygon ZIP,
then press Convert ZIP. Refresh its `/imports/<id>/` confirmation to see status,
attempt and errors. Dependencies remain pinned at the existing `/tmp/cpj-pcc`
checkout; loss of that local checkout causes a safe failure and needs operator
repair. No production/capacity claim. **Stopped before C08.** No commit or push.
