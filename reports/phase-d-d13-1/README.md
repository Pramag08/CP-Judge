# D13 — local PASS; retained Phase D complete

Completed by one sequential agent. **D13 and retained Phase D COMPLETE — local
PASS. Stop before Phase E.** D10/D12/D14/D15 remain deferred. Earlier D01–D09/D11
acceptance is reused from its existing reports; no import, conversion, package,
reference probe or participant judging was repeated. No commit or push.

The existing author preview now labels **Author preview / test mode**, lists the
selected statements, labels, limits and languages, and links private tests. Only
the owning author with current settings scope, or a superuser with explicit
contest settings/review scopes, can use it. Account administration alone is
insufficient. Each actor sees their own persisted test verdicts. Native statement,
asset, submission, judge, exact-version readiness and fixed scoring machinery are
retained; there is no separate executor or protocol extension.

Additive migration0012 stores an immutable version/source/runtime-bound private
receipt and retry key. Tests are archived native submissions with **no contest
object, participation or ContestSubmission**; native statistics already exclude
archived work. Admission locks the account and contest, checks session, scope,
selected approval, language, source size and queue/rate bounds; dispatch rechecks
the receipt through the existing C11 final packet gate. Native result/source/poll
and submission lists exclude these tests. Author/importer/tester knowledge and
retained conflict history prohibit official entry across scoped/native/direct
routes. Client test/official/virtual flags grant no authority. Admitted tests remain
private after scope/session changes; participant registration and [S,E) rules remain.

Checks and results:

- **6 focused MariaDB/HTTP tests PASS, 0 skips**, including scoped admin execution
  and statement assets, owner/participant/unrelated permissions, private polling,
  receipt retries, revocation, tampering, queue limits and constructed AC/WA score
  isolation. Constructed verdicts are separate from actual judging below.
- **11 relevant regressions PASS, 0 skips**: existing registration, withdrawal,
  timing, removal/DQ, races, conflicts and durable official-receipt boundaries.
- **Actual Chromium PASS**: existing `d07local2` author preview/statement/limits/
  languages; **submission24 CPP17 AC3/3 and25 WA3/3**, each dispatched once through
  the same isolated worker at0.5s/65536KiB. All6 callbacks/case rows agree with SQL;
  private verdicts survive a fresh login. Official participant standings and
  registration count display remain identical. Participants, removed entrant and
  unrelated author cannot use test mode; crafted test flags cannot bypass the
  ended contest, removal or native/direct submission rules. [Browser](browser.json).
- **Preservation PASS**: readable private full backup before migration;72 prior
  model sets /2220 non-session rows checked. Accounts, passwords, imports, source,
  cases, official scores/penalties/ranks/counts/solve statistics and native problem
  aggregates retained. The browser cleared one expired native navigation pointer;
  prior pointers were restored. Worker image/command/security settings and private
  config bytes match the retained C11 baseline. [Results](preservation.json),
  [checks](checks.json). Schema consistency and whitespace exit0.

Exact commands/exits, including failed setup/diagnostics: [ledger](commands.json).
From the repository root, the successful operations were
`python3 -B deploy/phase-d/run_author.py backup`, then `stage`, `migrate`, `tests`,
`regressions`, `stage`, `reload`, `bridge`, `shell author_fixture`, `credentials`,
`browser`, `preserve`, and final `stage`, `tests`, `check` with the same script
prefix. Each final command exited0. The ledger records underlying Docker argv.
Initial migration generation used the wrong container UID and the early test run
therefore lacked its table; corrected to existing UID1000 before successful
migration/tests. Preservation diagnostics corrected the expired navigation pointer
and selected the current C11 passive trace rather than historical B07 output.
No accepted browser submission was repeated. Final read-only `python3 -B -`
(changed Python AST, local Markdown links, acceptance records and final ledger
exits) and `git diff --check` both exited0.

Manual steps:

1. Sign in as the owning author at
   **http://127.0.0.1:8000/author/contests/**. Open the contest, then **Author
   preview / test mode**. Confirm selected statements, labels, limits and languages.
2. Open **Private author test**, follow **Preview statement**, return, enter a
   solution and click **Submit private author test**. Refresh until the real verdict
   appears; submit a wrong solution too. Re-login and confirm both private results.
   Existing proof: `/author/contests/d07local2/test/pv900000000000000002/`.
3. Compare participant standings and active official registration count before and
   after. As a participant/unrelated author, request the preview/test URL and POST
   test/official flags to test and ordinary/native submission URLs: access or
   timing rules must reject them. A scoped administrator uses the same test URL;
   global account-admin rights alone do not grant it.

Private credentials/source/screenshots/callbacks/backup/logs remain under ignored
`build/phase-d-d13-1/` or the existing private native trace. Production/load/crash
recovery, Phase E workspace, deferred grants/UI and rejudge/finalization remain
outside this proof. Existing upstream startup/MariaDB warnings remain visible.
