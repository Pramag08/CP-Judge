> Historical initial implementation below. Checkpoint1 is now integrated locally;
> current acceptance/activation/rollback/exposure summary: [checkpoint1](../phase-c-checkpoint1-1/README.md).
> Import/publication rows below remain pending/partial as recorded.

# Phase C — partial implementation, not complete

Phase C is **IN PROGRESS**. The live Phase B website still uses its original
settings and URL configuration. The new Django app is staged/tested, not enabled
on the live database. Do not infer live enforcement from these isolated tests.
C15 remains DEFERRED. Phase D was not started.

| Task | Acceptance status / actual evidence |
| --- | --- |
| C01 | PARTIAL: native first/last name, email and Profile reused; MariaDB round trip passes. Live private-profile integration pending. |
| C02 | PARTIAL: offline Django login and local superuser-attributed recovery command pass automated/Chromium checks on the isolated database. Live route replacement pending. |
| C03 | PARTIAL: explicit scoped capability helper and grant schema; policy tests pass. Native author/admin/direct routes and background exports not comprehensively gated. |
| C04 | PARTIAL: cross-contest roster/read/export and participant/admin-default denials pass helper tests; comprehensive URL/list/export/file/channel matrix pending. |
| C05 | PARTIAL: private upload core, owner access and streamed byte cap tested; author upload UI/HTTP multipart limits pending. |
| C06 | PASS for strict archive extraction/conversion acceptance: 15 focused archive tests plus existing six converter tests. Website upload integration remains C05. |
| C07 | PARTIAL: durable owner/status/error/attempt/findings schema; real synthetic conversion and failure/retry pass. Native background queue wiring, bounded scheduling and crash reconciliation pending. |
| C08 | PARTIAL: conversion findings persisted and explicitly distinguish conversion from judging; browser compatibility preview pending. |
| C09 | PARTIAL: inert HTML/raster/Polygon-math sanitizer passes four tests; native rendered-statement/browser asset authorization integration pending. |
| C10 | NOT IMPLEMENTED: recoverable DB/filesystem publication and rollback acceptance pending. Preserve B04/B05 installer. |
| C11 | NOT IMPLEMENTED: bridge version/hash readiness gate and stale-worker negative test pending. Online status is not sufficient. |
| C12 | PARTIAL: upload deduplication is owner-scoped; conversion retry is idempotent after ready. Concurrent publication/recovery acceptance pending. |
| C13 | NOT IMPLEMENTED: restricted selected-solution worker probe and real failure verdict acceptance pending. |
| C14 | NOT IMPLEMENTED: multiple selection, aggregate limits, bounded concurrency and independent publication/retry pending. |
| C15 | DEFERRED: external identity, Google, public signup and email delivery excluded. |
| C16 | PARTIAL: canonical ASCII IDs, DB uniqueness, temporary credential gate and concurrent provisioning pass isolated MariaDB tests. No legacy account was assigned/merged. Live activation and audited college-ID correction workflow pending. |
| C17 | PARTIAL: account-row generation serialization, login/password/reset/logout and per-request lock checks pass isolated tests, including concurrent login and Chromium replacement. Native transactional endpoints and event/channel gating remain open; no hardware binding claim. |

Checkpoint 1 evidence: [identity browser](identity-browser.json),
[organizer recovery browser](recovery-browser.json), private MariaDB test output
linked from [commands/exits](commands.json). Final suite: **32 tests, exit 0**,
including identity/races, scoped policy, recovery file-write rollback, upload core,
actual synthetic conversion and sanitizer. The initial 17-test run also passed;
an expanded 28-test run exposed a fixture-count assumption, fixed before the
29- and final 32-test successful runs. No failure is counted as a pass.

Checkpoint 2 evidence: **16 archive tests, exit 0**, rejecting traversal, absolute/
ambiguous/duplicate paths, case/Unicode directory collisions, symlinks/special
entries, metadata and actual streamed expansion violations, bombs and unsafe
extraction destinations, and dishonest entry-count metadata before ZipInfo allocation. ZIP64/multi-disk packages are explicitly unsupported. **Six converter regression tests, exit 0**, preserving
limits, standards, scoring, samples and inert attachments. No uploaded checker,
solution, validator, generator or script executed. These are conversion tests,
not judging. Checkpoints 3/4 and the final import → publication → submission →
verdict → standings browser smoke are **NOT RUN**.

## Reproduction

Run from repository root; Docker commands require existing project Docker access.
The checked site is commit `604d60cfd764bc708b04ffd75b715a5398b91f8b`;
converter pin remains `41ce3afcedf6c02793b308ba2e6ddb2ea5f82134`.
The initial converter command failed (exit1) because its temporary checkout was absent; the recorded pin was restored and the subsequent six-test runs passed. No dependency was installed in the converter venv or website runtime.

```sh
sg docker -c 'python3 -B deploy/phase-c/coordinator.py backup'
# Requires the pinned converter checkout at /tmp/cp-judge-pcc.
sg docker -c 'python3 -B deploy/phase-c/coordinator.py stage-tests'
sg docker -c 'python3 -B deploy/phase-c/coordinator.py test-identity'
.venv/bin/python -B -m unittest discover -s tests -p test_archive.py -v
PCC_ROOT=/tmp/cp-judge-pcc .venv/bin/python -B -m unittest discover -s tests -p test_conversion.py -v
```

Browser actions, in order after the isolated suite, are `browser-identity`,
`recover-browser`, `stop-browser`; initial setup refuses an existing browser
fixture. `resume-browser` retries a run only before its first password change;
it is not a general idempotent browser replay. Credentials/screenshots/session
state stay in ignored `build/phase-c-1/browser-*/`. The browser server is stopped.
The test database is `test_cpj_phase_c`; **never use test_settings/browser_settings
for the live site** (they use test-only fast hashers/cache).

Local organizer workflow (currently staged/test database only):
`python manage.py college_account provision|reset COLLEGE_ID --actor OPERATOR
--credential-file /absolute/private/new-file.json --settings=dmoj.cpj_browser_settings`.
It requires local operator access plus an active superuser actor, writes a new
0600 file, never prints the temporary credential, forces password change and
records an audit event. Output-write failure rolls back the password reset.
The configurable `CPJ_COLLEGE_ID_PATTERN` default accepts 1–64 ASCII letters,
digits, underscores/hyphens, starting alphanumeric. College-specific syntax must
be configured before real provisioning; no existing accounts are guessed/merged.

## Preservation and remaining work

[Private readable backup verification](backup.json) passes gzip round trip; a
full restore rehearsal did not run. An initial incorrectly captured dump reached
tool output; the replacement wrapper suppresses all contents and stores raw SQL
only under ignored mode-0600 files. No credential rotation/reset was attempted
on existing accounts.

[Final preservation](preservation.json) compares original vs current INSERT rows
privately: all account/password/profile, contest/entry/problem-assignment,
submission/source/testcase and applied-migration rows are identical. Live
Phase B retains **12 submissions / 1030 case rows**, its credentials and an online
worker. Phase C migrations ran only on the isolated test database. No commit,
push, external publication, volume removal or host security change occurred.

Next: finish C03/C04 native route and background-job scoping plus authenticated
revocable event access, then activate/check checkpoint 1 with a fresh backup.
The stock daemon's direct channel ports currently lack the A06 generation gate;
the new request middleware does not secure them. Continue C05/C07–C09 HTTP/UI/queue
integration before C10–C13; then C14 and the genuine integrated judging smoke.
These are unfinished implementation requirements, not passed security gates.
