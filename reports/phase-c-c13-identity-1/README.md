# C13 → C18 → C19 — sequential, one-agent bundle

**C13 PASS; C18 PARTIAL/BLOCKED; C19 PASS for independent password/session policy.**
Phase C remains incomplete. No commit/push, Phase D, limit change or UI redesign.

| Task/check actually run | Result |
| --- | --- |
| C11 prerequisite | Accepted historical evidence inspected; current authenticated worker/configuration verified after supported startup of stopped services. Existing pins/protocol/sandbox reused. [C11](../phase-c-c11-1/README.md). |
| C13 restricted probes | Owner plus scoped import/publication/CSRF checks; private known-solution registration/selection; version/source/runtime-bound execution, quotas and120s expiry/native-abort watchdog. Native execution records are archived, filtered from participant routes/lists/polls and have no ContestSubmission. Existing C10 version2 installed immutably on worker; native allowed languages remain empty, no participant visibility/contest assignment. Actual Chromium pending→**AC3/3 and WA3/3**, one native packet each, CPP17/0.5s/65536KiB; SQL/callback agreement. [Browser](c13-browser.json), [worker results](c13-live.json). |
| C18 safe identity work | Additive database-unique nullable canonical email; trim/lowercase entire ASCII address, Django syntax/254-character bound, preserve dots/+suffixes. Private inventory, audited admin provisioning/correction, guarded cutover and admission-only rollback retaining schema/data.6 DB identity/race checks, actual browser existing-password email login/wrong-password/session replacement/privacy PASS. Native profile/admin email read-only; public email-derived avatar hashes removed. [Browser](c18-browser.json). |
| C18 blocker | **4 existing accounts lack emails;0 invalid/0 conflict groups.** Five existing keys staged; one additional synthetic external acceptance account has its own key. Email-only mode remains OFF; transitional email plus legacy login preserves access. Organizer-verified corrections required for IDs recorded only in ignored `build/phase-c-c13-identity-1/c18-private-inventory.json`. No existing address guessed, merged or reassigned. [Counts](c18-inventory.json). |
| C19 | Forced first/reset redirects and import/export gates removed; historical flag values/audits retained. Voluntary change remains. Verified outside-app organizer reset requires active account administrator, reason/verification attestation, private credential output, secure native hashing, audit and generation revocation. No email/token service. Actual provisioned external email login (no college ID), organizer reset, old-password/stale read/POST/poll rejection, replacement session, no forced redirect and voluntary change PASS. Only the synthetic acceptance account was reset. [Browser](c19-browser.json). |
| Migration/rollback | Fresh private full readable backups before probe/email schema and C19 policy changes. Isolated0006→0008 migrations preserve existing password; operational rollback retains intervening accounts/password reset/submission/source/audit and revokes sessions. No stale database restore; additive schema retained. Backup restore itself NOT TESTED. |
| Final focused checks | **16 passed,0 skips**:2 probe,6 email/privacy/race,6 password/session,1 migration/rollback,1 C17 in-flight admission race. The27 C11 regressions also passed after probe dispatch changes. Migration consistency, deployed source hashes and whitespace exit0. [Checks](final-checks.json), [exact commands/exits](commands.json). |
| Judging continuity/preservation | One new normal native participant submission **19: AC103/103**, CPP23/2s/262144KiB, one dispatch/103 callbacks; browser status/list agree. It uses native virtual practice in the ended fixture contest. Browser retries resumed19 read-only, never resubmitted. **64 original model sets/1900 non-session rows** checked; existing account PKs/hashes/emails/college history, results and official standings preserved. Native reconnect rebuilds runtime row IDs with identical values; fixture profile pointer restored. Container IDs/images/configuration/mounts/sandbox match C12, normalizing only unset worker DNS `null`/`[]`. Original worker problem bytes preserved. [Browser](participant-browser.json), [preservation](preservation.json). |

Operator driver: `sg docker -c 'python3 -B deploy/phase-c/c13_bundle.py ACTION'`.
Final successful actions (exit0): `backup`, `stage`, `migration`, `install-probe-version`,
`bridge-reload`, `reload`, `browser c13`, `shell c13_verify`, `backup-next c18`,
`shell c18_inventory`, `browser c18`, `backup-next c19`, `shell c19_prepare`,
`c19-live retry1`, `participant-browser`, `shell c19_preserve`, `final-checks`.
Focused command uses `tests` followed by the two named `cpjudge.c13_tests.ProbeTests`
methods, `cpjudge.c18_tests.EmailTests`, `cpjudge.c19_tests.PasswordPolicyTests`,
`cpjudge.migration_acceptance_tests.MigrationAcceptance` and
`cpjudge.integration_tests.NativeRaceTests.test_inflight_request_serializes_replacement_login`.
Exact arguments, failed attempts and final exits are retained in the command ledger;
raw logs/backups/credentials/source/screenshots remain ignored under `build/`.

Failures corrected before acceptance: staging UID/read-only-copy handling; browser
navigation/reload waits/selectors/referrer policy; migration fixture limits; missing
CSRF in a stale-POST test; public-handle versus email test URL and polling-page idle
wait; concrete native avatar-hash leak. The first browser reset attempt stopped on
its missing CSRF token; a second audited reset of the **same synthetic fixture**
verified the corrected request, with original accounts untouched. Preservation
checks use the existing C11 rules for native runtime IDs/unranked fixture context.
Final watchdog/source guards were loaded while idle; expiry helpers were tested,
but no live120s expiry/in-flight loss experiment was run.

Authorized operator workflow uses native management commands `email_account`
(`inventory`, `stage`, `provision`, `correct`, `cutover`, `rollback`) and
`account_password_reset`, with `--actor-id` and operator-owned0600 JSON input/output
files. Correction input keys: `user_id`, `email`, `reason`; reset input keys:
`user_id`, `reason`, `requester_verified` (true only after outside-app verification).
Inventory/credential output must be a NEW private file; never pass addresses or
passwords in shell arguments. Resolve the four existing accounts, re-inventory/stage,
then explicitly request guarded cutover acceptance. Rollback changes admission and
revokes generations; retain additive schema and intervening data, never replay old
passwords or restore a stale database.

Remaining: C18 email-only cutover and integrated **same-version** import→probe→
participant submission→standings evidence. The separate AC103 continuity check does
not supply that integration. C12 acceptance is reused; C14/C15 remain deferred,
C16 historical evidence and C17 single-active-session policy remain. No physical
binding, production/capacity/crash recovery or original111MiB package claim;
32MiB upload/128MiB conversion limits unchanged.
