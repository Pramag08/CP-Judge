# Phase C checkpoint 1 — integrated local PASS

C01–C04/C16/C17 are enabled on the actual local DMOJ site. Import/publication
checkpoints remain pending; no Phase D work, commit or push. Reused the existing
Phase C app, native authentication/models/templates/admin, Celery and judge.

| Task | Actual acceptance |
| --- | --- |
| C01 | PASS: existing User name/email and Profile reused; owned native profile round trip; unauthorized roster/email denials. |
| C02 | PASS: real local login/forced password change and offline organizer recovery in Chromium; no external identity/email dependency. |
| C03 | PASS: scoped native contest admin/list/create/edit, direct requests, source/results/private-file denials, scoped exports and real Celery execution checks. Unscoped legacy management surfaces fail closed. |
| C04 | PASS: participant/author/account-admin and A/B scope matrix through native URLs and live Chromium; known private object/channel IDs do not grant access. |
| C16 | PASS: canonical ID uniqueness/provisioning race; audited correction/assignment and concurrent-correction collision; old ID reservation, no merging or password change. |
| C17 | PASS: serialized generations/admission, concurrent logins, stale AJAX/poll/logout, password change/reset/disable, revocation and native unranked conflict checks. No device binding. |

The native integration suite passed **22 tests**, then **3 targeted final checks**
passed (correction race, native unranked join after revocation, scoped delegation).
Some checks overlap; these are not 25 distinct tests. Recorded final successful
commands exited **0** in [commands.json](commands.json); failed attempts remain
recorded and are not counted as passes. Prior helper/import suites were reused,
not presented as native acceptance.

Live evidence: [role/session/export browser](browser.json),
[recovery/correction](recovery-browser.json), [legacy login](legacy-browser.json),
[real Celery stale-job denial](stale-export-job.json),
[final native source/result/channel matrix](final-access-browser.json).

**Actual judging:** fresh native browser submission **14**, CPP23, **103 AC/103**;
[display/polling](judging-browser.json) and [preservation/native callback checks](acceptance.json)
agree. The first smoke exposed dispatch before transaction commit: submission13
had zero executed cases and became native IE on worker disconnect. Its evidence
is retained in [dispatch-failure.json](dispatch-failure.json). Dispatch now runs
on commit; rollback never dispatches. This is not an interrupted-job recovery or
rejudge acceptance claim. Earlier browser selector/setup failures are retained.

## Activation, legacy accounts and operations

A [fresh private readable backup](backup.json) preceded real migrations
`cpjudge.0001`–`0004`. Full gzip readback passed; database restore was **not tested**.
Live settings use Django PBKDF2/default work factor, no test hashers/cache/settings.
Original account password hashes, source/results/contests and immutable judge
files/configuration remain unchanged across 56 baseline model comparisons. Only
native login/access timestamps, worker liveness and problem statistics changed.

Existing accounts retain exact legacy usernames/passwords with **no guessed ID**.
Their next login creates a generation record with a null college ID. Once a
registrar explicitly assigns/corrects an ID, login uses that canonical ID; the
native User PK/username/password/history remain unchanged. Old IDs stay reserved.
Syntax is configurable through `CPJ_COLLEGE_ID_PATTERN`; normalization remains
outer trim + ASCII uppercase, rejecting Unicode/collisions without merging.

Run from repository root with existing project Docker access:

```sh
sg docker -c 'python3 -B deploy/phase-c/c1.py tests'
sg docker -c 'python3 -B deploy/phase-c/c1.py targeted-races'
sg docker -c 'python3 -B deploy/phase-c/c1.py lifecycle-check'
sg docker -c 'python3 -B deploy/phase-c/c1.py verify'
```

`tests` now discovers the two subsequently added final cases too. Test settings
are confined to `test_cpj_phase_c`. Do not repeat fixture/reset/submission actions
blindly: receipts refuse duplicate POSTs. Private browser/session/source/log/backup
artifacts are under ignored `build/phase-c-checkpoint1-1/`.

Trusted local operators can use native `python manage.py` inside the site:
`college_account provision|reset ID --actor ADMIN --credential-file /private/new.json`
(with optional name/email/author fields),
`correct_college_id USER_PK NEW_ID --actor ADMIN --reason REASON`, and
`contest_grant CONTEST USERNAME CAPABILITY --actor GRANTOR [--revoke]`.
Local OS/container access authenticates the operator; `--actor` is audited
attribution and must be an authorized active administrator/grantor. Temporary
credentials go only into new 0600 files; write failure rolls back reset. Login and
reset operations are rate limited. Scoped grants never create platform admins.
The temporary elevated test account is disabled; private c1livea/b, ordinary/scoped
fixture accounts and both new native attempts are retained for review.

Browser updates now use authenticated one-second database polling and native
result widgets. Every poll rechecks session generation and current scope. The
unauthenticated daemon is stopped, ports9995/9996 are closed, and managed startup
cannot reopen them. Native legacy task/global API/package-management surfaces
without sufficient scope context are disabled; scoped roster jobs reauthorize at
execution and download. Native hidden case output/checker feedback is suppressed
in responses while stored evidence is preserved. Statement/asset handling remains
B06; import/publication functionality was not activated.

## Rollback and exposure

Rollback: `sg docker -c 'python3 -B deploy/phase-c/c1.py rollback'` stops services,
restores the private prior settings and leaves the site stopped. It preserves the
DB, new results and additive schema; **never load the old dump over new work**.
Keep the enabled marker and event daemon stopped. Normal startup fails closed if
the checkpoint policy is absent. Repair/review and re-enable the overlay before
serving HTTP. This rollback procedure is documented and syntax checked, **not
executed** against the final live site.

[Local exposure assessment](exposure.json): treat the earlier dump/tool transcript
as containing account identifiers/contact data/password hashes, session records,
worker registration authentication material, profile/IP/authentication metadata,
private problem/contest/entrant data, submitted source, compiler diagnostics and
case records (including saved feedback/output). Values were not reproduced.
Account plaintext passwords are not stored in auth_user. The authorized exposure
remediation is now complete for the worker key and sessions; see [sanitized
rotation evidence](exposure-remediation.json), [key/config consistency](exposure-key-consistency.json),
and [post-rotation judging](exposure-remediation-submission.json).

The old worker credential was rejected in an actual pinned-worker handshake and
the replacement authenticated. Host credential/config, bridge registration and
native database record agree; all are private. Worker image, container settings,
problem mount and sandbox policy are unchanged. Before rotation, a fresh full
database backup was gzip round-trip checked and kept mode0600 under ignored
`build/`; it remains private. Rotation deleted **23** stored session rows and
incremented **6** identity generations. The captured pre-rotation browser cookie
then received HTTP401; the same existing legacy account password still logged in.
Existing account hashes/passwords, college IDs, submissions/results and contest
data were preserved. No password was reset.

After reconnect, actual browser submission **15** reached the real worker and
returned AC on all103 cases (103/103 points); authenticated polling updated the
page with no browser errors. The final prior-row/problem/sandbox preservation
check exited0. Commands: `sg docker -c 'python3 -B deploy/phase-c/c1.py rotate-exposure'`,
`sg docker -c 'python3 -B deploy/phase-c/c1.py verify-rotation-config'`,
`sg docker -c 'python3 -B deploy/phase-c/c1.py verify-rotation-submit'`, and
`sg docker -c 'python3 -B deploy/phase-c/c1.py verify'` (final runs exit0).

The exposed transcript still needs restriction/removal through its owning
interface where available; this project cannot delete an existing Codex
transcript. The earlier transcript may still contain account password hashes and
private records; assess whether its audience was untrusted. The old worker key may
remain in access-restricted historical private database backups. No account
password was rotated as part of this authorized remediation. `manage.py status`
currently has an older anonymous `/status/` probe that receives401 under the
checkpoint's route gate; worker readiness was verified through the native database,
bridge handshake and browser submission instead.

Limits: local HTTP/development server (Secure cookies require HTTPS), one trusted
worker, bounded local fixtures; no production/perfect-security/capacity claim.
Full contest lifecycle/delegation UI and import/publication/probe/multi-ZIP
acceptance remain future tasks. **Next: checkpoint2 only on request; stop here.**
