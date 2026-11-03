# C05 — private single-ZIP upload

Review follow-up: inspected the actual middleware, views, storage core and tests.
Fixed unbounded draining of rejected terminated streams, missing total-body read
limits (including fields/trailing bytes), and cleanup that could unlink an
existing file after a generated-name collision. Rejections now stop draining;
a body wrapper caps reads at the ZIP limit plus64KiB framing, with at most one
extra byte for detection. Cleanup only unlinks a file created by that attempt.
Storage errors also return a generic response without internal paths.

The expanded **8-test suite passed**, covering multipart parser limits,
interrupted-write/database-failure cleanup, collision preservation, revoked grants,
stale sessions and owner deduplication. Chromium/HTTP checks, private-storage
verification and the existing data/worker preservation verifier passed after an
HTTP-only reload. No migration or existing-data deletion was performed.
Process-crash/outer-transaction rollback reconciliation of filesystem orphans is
still unimplemented. Upload duration, aggregate disk quota and concurrency limits
are not established by C05. Terminated WSGI streams are covered by native tests;
the actual local HTTP server rejects unframed/chunked requests with411.

**COMPLETE — PASS for the local C05 acceptance below.** The existing `ImportJob`
model and private upload core were reused. DMOJ now serves an authorized upload
form at `http://127.0.0.1:8000/contest/c1livea/import/`. Uploads are limited to
one ZIP per request; configured compressed-size limit is **32 MiB**.

The live app checks the current session and contest `problems.import` grant before
reading the POST body. Django CSRF remains enabled. A streaming file handler counts
received bytes, independent of `UploadedFile.size`; declared oversize requests are
rejected before parsing. The upload core counts bytes again while storing. A
bounded preflight checks ZIP structure before creating the record. It does not
extract, convert, publish, execute or enqueue the package.

Uploads are written to `/app/private-cpj-imports`, outside static/media roots,
under a random server-generated name. The directory is mode0700 and the ZIP file
mode0600. Each `ImportJob` stores its owner, contest, content digest and status.
The confirmation route survives refresh, and the private download route rechecks
the owner and current grant. Failures remove partial files and do not create a
misleading upload record.

## Actual checks

| Check | Result |
| --- | --- |
| Focused native HTTP-boundary suite | **PASS, 8 tests, exit 0**: scoped author/admin access, participant/anonymous denials, confirmation/download ownership, CSRF, malformed/multiple files, cleanup and byte-count handling with missing and understated lengths. |
| Chromium author flow | **PASS**: valid ZIP upload, confirmation refresh, owner download; response403 for missing/invalid CSRF; actionable400 errors for missing/non-ZIP/malformed/multiple files;413 for declared oversize; anonymous/participant/cross-contest denials; public static/media denial. |
| No trustworthy request length | **PASS, fail closed**: local HTTP server returned411 for unframed and chunked requests. A WSGI-terminated stream with absent and understated length was parsed through the actual upload handler; 1025 bytes against an 1024-byte test limit returned413. |
| Storage and failed-request cleanup | **PASS**: exactly one owner-associated `uploaded` row and one private ZIP remain after rejected requests; attempt0, no findings/error, correct file modes, path outside public roots. |
| Prior checkpoint preservation | **PASS**: `c1.py verify` exit0 after C05; existing account hashes, submissions/results, worker image/configuration, sandbox and immutable problem files passed the established comparison. |

Final successful commands from the repository root:

```sh
sg docker -c 'python3 -B deploy/phase-c/c05.py tests'
sg docker -c 'python3 -B deploy/phase-c/c05.py browser'
sg docker -c 'python3 -B deploy/phase-c/c05.py verify'
sg docker -c 'python3 -B deploy/phase-c/c1.py verify'
python3 -B -m py_compile deploy/phase-c/c05.py deploy/phase-c/c05_browser.py deploy/phase-c/cpjudge/uploads.py deploy/phase-c/cpjudge/views.py deploy/phase-c/cpjudge/integration_tests.py
git diff --check
```

The first four commands exited0 in their final runs; compilation and diff checks
also exited0. Detailed exit ledger is [commands.json](commands.json), sanitized
browser matrix is [browser.json](browser.json), and storage verification is
[storage.json](storage.json). Earlier failed explorations are retained in ignored
private logs and are not counted as passes.

No schema migration was needed, so no migration backup was taken. Only the site
HTTP process was restarted; the worker, bridge, Celery, DB and sandbox were not
restarted or reconfigured. A task-owned `C1LIVEA` author fixture received the
explicit contest import grant; one small synthetic ZIP and its confirmation
record remain for manual review. No prior credentials or judging data changed.

## Manual test and limits

Sign in as an author with `problems.import` on contest `c1livea` and open
`http://127.0.0.1:8000/contest/c1livea/import/`. Select one `.zip`, submit, refresh
the confirmation page, then try the private download link. The task-owned browser
account details remain in ignored `build/phase-c-checkpoint1-1/accounts.json`;
no password is included here.

The local Django WSGI development server does not expose chunked request framing
to the application, so requests without a usable length receive411. Where a WSGI
server marks input as terminated, the app-level handler enforces the actual file
byte limit while reading. This is a local proof, not a production upload-stack
capacity or security certification. C07 conversion/job processing, C08 preview,
C09 rendered statement integration and C10+ publication remain pending; C15 stays
deferred.
