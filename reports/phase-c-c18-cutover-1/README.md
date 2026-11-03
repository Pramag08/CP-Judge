# C18 email-only cutover — local PASS / Phase C scoped closure

**C18 COMPLETE; Phase C COMPLETE for retained local gates.** C14/C15 remain
DEFERRED. No Phase D, commit/push, new judging, password reset/change or email delivery.

The user explicitly assigned the four existing native development fixtures
(IDs1/2/7/8). The private worksheet records `organizer_assigned_development`, with
`verified_by_organizer=false`, `mailbox_verified=false` and
`real_participant_identity=false`. These are organizer-assigned development
addresses, **not verified mailboxes or real participant identities**. Values remain
in ignored mode0600 files/native private account fields, not this report.

The existing mapping workflow was extended only to accept that explicit provenance
without falsifying verification. Fresh readable full private backup before data
changes; `check` and `apply` exit0. All four assignments applied atomically through
the audited correction service/unique canonical key. Added3 identity rows for
previously unmapped native accounts; native account IDs/roles unchanged. Re-inventory
and staging found **10 canonical keys,0 missing/invalid/conflicting identities**.
The existing guarded `email_account cutover` enabled email-only mode and revoked
all existing session generations. No live schema change or password operation.

| Acceptance actually run | Result |
| --- | --- |
| Browser before cutover | Existing admin/participant legacy passwords still worked after mapping; actual sessions saved privately for revocation proof. |
| Browser after cutover | All4 email/password logins pass, including case/whitespace normalization; unchanged passwords. All4 username logins fail. Native admin entry redirects to the email form; username rejected, email admin/account access succeeds. Direct native-admin username POST cannot authenticate. |
| C17/C19/privacy | No forced-change redirect for any of the4; voluntary change form available, not submitted. Wrong password fails. Actual pre-cutover/replaced sessions reject read/POST/poll/admin/stale logout; replacement remains valid. Own existing submission/status/source access and other-email/admin privacy pass. Contact-only recovery; no email/token service. |
| Focused isolated checks | **15 passed,0 skips**:3 provenance/ordinary-admin routes/local recovery;6 session/password tests under email-only mode (including concurrent logins/reset revocation);6 canonical normalization/privacy/provisioning/correction races. Resets/changes in these synthetic test-DB checks do not touch live users. |
| Preservation | **68 prior model sets/2089 non-session rows**, all10 old password hashes/usernames/IDs/college-ID history/roles/permissions and prior source/cases/contests/standings/audits preserved. Exactly4 correction,1 staging and1 cutover audits added. Only4 assigned email/key fields, normal access/generation/liveness activity and restored ended-fixture navigation context differ. |
| Source/operations | Deployed identity source agrees; migration consistency/AST/whitespace pass. Native settings/backend retain C17 locks/hash checks. No new dependency, worker configuration, package size or scoring change. Backup gzip readback passed; full backup restore not performed here. |

[Cutover receipt](cutover.json), [browser before](browser-before.json),
[browser after](browser-after.json), [direct admin POST](browser-admin-route.json),
[preservation](preservation.json), [checks/source identities](checks.json),
[exact commands/exits](commands.json), [retained-gate closure inspection](closure.json).
Private backup/credentials/cookies/screenshots
and original blank worksheet remain ignored under `build/phase-c-c18-cutover-1/`.
One initial preservation assertion rejected the3 legitimate additive identity rows;
it was corrected to require exactly the previously unmapped native fixture accounts,
and the complete preservation check passed. Failed command retained in ledger.

Driver from repository root:
`sg docker -c 'python3 -B deploy/phase-c/c18_cutover.py ACTION'`.
Final actions exit0: `snapshot`, `stage`, `tests cpjudge.cutover_tests.CutoverTests
cpjudge.cutover_tests.EmailOnlySessionTests cpjudge.c18_tests.EmailTests`,
`prepare-mappings`, `check-mappings`, `apply-mappings`, `reload`,
`browser-credentials`, `browser before`, `shell c18_cutover_activate`, `browser after`,
`browser admin-route`, `shell c18_cutover_preserve`,
`shell c18_local_recovery_prepare`, `finish`.

Local administrator recovery is preserved. With trusted local Docker/operator
access, active administrator actor1, and the prepared site-owned0600 reason-only
file, explicitly restore transitional login without changing passwords/data:

```sh
sg docker -c 'docker exec cpjudge-b01-site python manage.py email_account rollback --actor-id 1 --private-file /app/private-cpj-ops/c18-local-recovery.json'
```

This deliberately enables legacy login again and audits/revokes generations; then
`b01-staff` with its existing password can reach local admin. Email login and all
canonical mappings/intervening data remain. The file was prepared/permission-checked;
**live rollback was not executed**. Recovery/guarded re-cutover was rehearsed in the
isolated native database with hashes/intervening data preserved. After resolving
the incident, use `email_account stage` and guarded `cutover` with a NEW private
reason file; never restore a stale database or replay credentials. Forgotten-password
recovery remains the separate authorized outside-app verified administrator reset
in [C19](../phase-c-c13-identity-1/README.md); no reset was performed for this cutover.
No ordinary web username bypass exists while email-only mode is active.

Retained acceptance was inspected/reused, not rerun or relabeled as new tests:

| Retained gates | Accepted evidence |
| --- | --- |
| C01–C04/C16–C17 | [Native checkpoint1](../phase-c-checkpoint1-1/README.md); historical ID/forced-change evidence retained; C18/C19 replace current login policy. |
| C05/C06/C07/C08/C09 | [Upload](../phase-c-c05-1/README.md), [extraction](../phase-c-c06-1/README.md), [conversion jobs](../phase-c-c07-1/README.md), [findings](../phase-c-c08-1/README.md), [sanitized statements](../phase-c-c09-1/README.md). |
| C10/C11/C12 | [Immutable private publication](../phase-c-c10-1/README.md), [actual readiness](../phase-c-c11-1/README.md), [retry/concurrency/deduplication](../phase-c-c12-1/README.md). |
| C13/C19 | [Actual private AC/WA probes and no-forced-change/session policy](../phase-c-c13-identity-1/README.md), plus current email-only browser/session regressions above. |
| Same-version integration | [Existing import/version2/probe17→official20 WA3/21 AC3/22 AC3→manual/browser/SQL standings](../phase-c-integrated-1/README.md). Receipts/manifests/results preserved; no rejudge. |
| C18 | Current complete canonical inventory, applied development provenance, guarded cutover/browser/admin/recovery/uniqueness/preservation evidence above. |

All17 retained C01–C13/C16–C19 gates and the integrated smoke have local evidence;
C14/C15 are deferred, not passed. This does not complete M2/full MVP or general
contest/lifecycle/deployment/capacity/crash-recovery work. Existing32MiB upload/
128MiB conversion limits still exclude the original111MiB package; no claim for
that unsupported package, real participant identity verification or production use.
