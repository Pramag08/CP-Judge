# Same-version integration and local email worksheet

**Integrated local PASS; C18 email-only cutover remains BLOCKED.** One agent;
no password/email changes, reset, new account, commit/push or general Phase D UI.

Reused C07/C10/C12's existing upload/conversion/publication and C13's actual private
AC probe. Chromium downloaded/re-uploaded the same owner-bound archive and returned
to **job24/attempt2/version2** (`pv900000000000000002`), with unchanged package and
manifest digests. Browser confirmed probe1/execution17 remains AC3/3 and verified.
No repeated conversion/probe or substituted legacy problem.

The missing participant path needed one additive `ContestVersionAdmission` record
and guarded native adapters: owner/scoped approval before start, complete full-AC
probe/source/version/runtime validation, frozen private contest rules, allowlist,
official entry and server receipt window. Native allowed-language metadata becomes
CPP17 through that separate approval; the immutable manifest/judge files/hash stay unchanged and the
native Problem remains private. A probe alone still grants no participant
access. C11 performs fresh authenticated worker file/compiler/checker checks at
selection/final send, including exact official receipt and source validation.
No new native protocol fields or execution on the coordinator; no worker/sandbox,
package limits or scoring changes. This is bounded private acceptance admission,
not completion of general contest management/publication/lifecycle tasks.

Actual browser → native bridge → existing worker → callbacks/SQL → browser:

| Official submission | Entrant | Result | Executed cases |
| --- | --- | --- | --- |
|20|C1LIVEP|WA|3/3 WA|
|21|C1LIVEP|AC|3/3 AC|
|22|C1LIVEQ|AC|3/3 AC|

Each dispatched once on the **same native version**, CPP17/0.5s/65536KiB;9 actual
case callbacks agree. Both entries are native LIVE/official (`virtual=0`), in the
new private `cintlocal1` fixture. Private probe17 has no ContestSubmission and never
contributes to standings. Repeated browser runs resume the existing receipts and
never resubmit them. Participants cannot access the probe/package/other source;
unrelated author receives denials. Original unreleased versions remain denied.

Hand calculation and both browser standings/SQL agree:

| Rank | Entrant | Solved | Penalty |
| --- | --- | --- | --- |
|1|C1LIVEQ|1|510s elapsed|
|2|C1LIVEP|1|499s elapsed +1200s prior WA =1699s|

[Actual chain/rows/preservation](proof.json), [browser](browser.json),
[final checks/source hashes](checks.json), [exact commands/exits](commands.json).
**67 original model sets/2049 non-session rows** checked: every existing password
hash/email/account ID, college-ID history, audits, prior submission/case/official
standings row preserved. Only expected native access/generation/liveness/AC-rate
activity changed; original fixture navigation pointers restored and new official
entries/results retained. Fresh full private gzip backup before schema/data change;
backup restore itself NOT TESTED. Old immutable versions/manifests/files verified.

Checks actually run:4 new admission negatives +27 C11 regressions (**31 PASS**),
then **9 final focused checks,0 skips**:4 approval/entry/hash/source/rules/complete-
case guards,2 C13 privacy/expiry checks, C19 historical flag/first-login regression,
C17 in-flight admission race and isolated additive migration/operational rollback.
The existing migration rehearsal now follows the current leaf so the new additive
schema survives its data-preserving rollback test. Deployed source agreement,
migration consistency, both DOM/manual/SQL standings, syntax and whitespace pass.

Commands from repository root use
`sg docker -c 'python3 -B deploy/phase-c/integrated.py ACTION'`:
`snapshot`, `stage`, `migrate`, `tests <named test paths>`, `reload`, `bridge-reload`,
`shell integrated_fixture`, `browser`, `shell integrated_verify`, `finish`.
Final executions exit0; exact test paths are in the ledger. Corrected acceptance
attempts retained there: expected403/404 distinction, q's C16-corrected college ID
(use its existing email login), native join confirmation, executor database ID
rather than display-label guess, and native ranking-table selector. No password
was changed to fix a test. Private raw logs/source/screenshots/backup remain ignored
under `build/phase-c-integrated-1/`.

The four blockers are existing local test accounts with **blank**, not conflicting,
emails: ID1 `b01-staff` (baseline admin), ID2 `b01-participant` (baseline participant),
ID7 `b10tmpa`, ID8 `b10tmpb` (B10/B11 entrants with retained submissions/standings).
Existing mapped accounts already support email login; these four block the
**email-only cutover**. Their accounts/credentials/history must not be guessed,
merged or reset to fill the inventory.

Private blank worksheet: `build/email-mappings-1/mappings.json` (mode0600, Git ignored).
Keep IDs/usernames. Fill each empty `email` with the organizer-verified personal
address, add an audit `reason`, and set `verified_by_organizer` true only after
verification. No sample/fabricated address is supplied.

```sh
python3 -B deploy/phase-c/email_mappings.py check
python3 -B deploy/phase-c/email_mappings.py apply
```

`check` rejects the current four blank rows, exit1 as expected, without DB changes.
Filled validation/apply awaits organizer input and was NOT run on live identities.
The wrapper requires the protected file and authorized administrator (default actor1;
`--actor-id` can select another authorized admin), backs up before apply, uses the
existing audited correction service and DB uniqueness, and applies all four
atomically. Password hashes remain unchanged. Corrections revoke affected sessions;
the same passwords/legacy credentials can sign in again. Email-only mode stays OFF
**even after apply**; cutover is a separate guarded operation/acceptance request.
No addresses/passwords in shell arguments, output or public reports.

Phase C remains incomplete solely at the recorded identity cutover gate; integrated
same-version evidence is now complete for this scoped package/runtime. C12 remains
passed, C14/C15 deferred, C16 history/C17 behavior retained. Original111MiB package
remains outside unchanged32MiB upload/128MiB conversion limits. No general capacity,
crash recovery, arbitrary package/runtime or production/deployment claim.
