# Minimum native website review — documentation complete, implementation pending

2 November 2026; one agent. The final instruction “no implementation for now”
limits this task to source/evidence inspection and documentation. No application,
service, schema, account/password, limits, private package or runtime change. No
new conversion, browser journey, actual judging, deployment or load test ran.

Reused: pinned DMOJ site `604d60cfd764bc708b04ffd75b715a5398b91f8b`, native Ace,
problem/submission/case/list/standings pages, polling and isolated judge; retained
custom strict imports, immutable-version readiness, identity/session/scope guards,
atomic contest receipts, fixed scoring and private author tests. Source inspected:
`build/a09-site-1/site/{templates/problem/submit.html,judge/forms.py,judge/views/contests.py,judge/models/submission.py,judge/admin/submission.py,judge/admin/contest.py,judge/bridge/judge_handler.py}`;
`deploy/phase-c/cpjudge/{urls.py,native.py,navigation.py,entries.py,views.py,contest_manage.py,templates/cpjudge/}`.
The site checkout exists and its HEAD matches the recorded pin; local patches
remain intentional. No clean-up or pin update was performed.

| Finding | Smallest planned action; not implemented |
| --- | --- |
| Home already redirects to native contest list; native visibility adapter filters eligibility/removal; top nav currently only Contests | Finish scoped author/account links and verify eligible list/actions/counts/empty states rather than build a new homepage backend. |
| Managed overview includes problems and Standings link; ranking template has no common tabs | Add Problems / My Submissions / Standings links to native/scoped routes, with current-account/current-contest filtering. |
| Managed submit extends native Ace form and supplies durable retry key | Reuse form/admission; verify fallback and complete file-widget path. No file chooser found in inspected form/template; add bounded file-to-source loader only if absent. |
| Native Ctrl-S/restore uses `submit:<language>` | Isolate retained saved code by account/contest/problem/language; test shared-browser account separation. No new draft service. |
| Native own lists, case redaction and session/scope-checked polls already exist | Exercise current routes in final browser journey; fix concrete privacy/usability blockers only. |
| Native rejudge/reversion exists, but current admin allowlist blocks its actions; callbacks address submission IDs | Verify scoped action, old case/history retention, pending credit and serialized/stale-result safety before enabling. Native presence alone does not prove F10/F11. |
| No managed finalization route found; existing roster export is a different function | Inspect remaining native coverage, then add only missing provisional/final/pending-error guard and results export if required. |

Changed documentation: plan/dependency closure now favors native reuse; Monaco,
split layout, new draft sync/autosave, custom Run, extra languages and redesign
are deferred. Separate local H03 journey from college-server readiness; internet
independence and fixed capacity targets are not prerequisites. UI and Run contracts
record that scope without changing historical evidence. Full classification and
ordered edges: [dependencies](../../MVP_DEPENDENCIES.md).

Historical results inspected, not rerun: [Phase C closure](../phase-c-c18-cutover-1/README.md)
(email-only/session/recovery), [same-version integration](../phase-c-integrated-1/README.md)
(probe17 → official WA20/AC21/AC22 → checked standings),
[D01–D06](../phase-d-d01-d06-1/README.md) (8 focused checks and browser publication),
[D07–D09/D11](../phase-d-d07-d11-1/README.md) (10 focused/12 regressions, participant23 AC3,
registration/removal/DQ), [D13](../phase-d-d13-1/README.md)
(6 focused/11 regressions, private author24 AC3/25 WA3, unchanged official standings).
These passed their original boundaries; the newly requested combined H03 journey
and native-tools operations acceptance remain **PENDING**.

Checks this review: `git status --short` exit0 (existing dirty work preserved),
`git -C build/a09-site-1/site rev-parse HEAD` exit0 (pin above), source reads/searches;
some exploratory paths did not exist (exit1/2), then corrected to actual
`deploy/phase-c/cpjudge/` and upstream `judge/views/contests.py` paths.
Documentation verification: `python3 -B /tmp/cpjudge_minimum_check.py` exit0
(local changed-document links and task-row presence), `git diff --check` exit0.
No runtime pass is inferred from these checks. No new evidence framework added.

Local URLs/manual path (known routes, current availability not probed):

1. Author: sign in at http://127.0.0.1:8000/accounts/login/ with existing personal
   email/password; open http://127.0.0.1:8000/author/contests/ and Create contest.
   Save a future schedule; use Import Polygon ZIP, upload one supported bounded
   ZIP, convert, inspect compatibility and safe preview, privately publish version
   and run an accepted known-solution probe. Select/reselect the exact version,
   set label/order, preview and publish contest with live worker checks.
2. Author unranked tests: use Author preview / test mode → Private author test;
   submit and check private persisted verdicts and unchanged official standings.
   Existing ended fixture: http://127.0.0.1:8000/author/contests/d07local2/preview/.
3. Participant: email login → http://127.0.0.1:8000/ → eligible contest → Register
   before start or permitted late entry → Problems → native statement/Submit →
   enter source and enabled language → Submit → status/cases → Standings.
   Existing ended fixture: http://127.0.0.1:8000/contest/d07local2 and
   http://127.0.0.1:8000/contest/d07local2/ranking/.
4. Use a fresh contest schedule for new live judging; do not extend/reset expired
   fixtures. My Submissions tab, account-safe saves and source-file chooser still
   need the targeted work above. As an unrelated/removed user, direct/poll/source/
   asset/submit/rejoin requests must fail. Never publish credentials/raw evidence.

Remaining local work: targeted E navigation/editor privacy/file handling and new
combined H03 journey; bounded F rejudge/finalization/export checks remain unaccepted.
No external information blocks local planning. Original **111 MiB ZIP unsupported**
under unchanged **32 MiB upload / 128 MiB conversion** limits. Missing logo is
nonblocking. Implementation is intentionally stopped at the user's boundary.

Separate college-server checklist (not executed): production configuration and
supported pins; approved reachable campus network; fresh isolated backup/restore;
compile/execution interruption and worker recovery; representative measured event
load. One server with isolated worker suffices; internet allowed; no second laptop,
fixed 150+/300 guarantee, public exposure or host-network changes. Later work needs
server access/configuration, campus network approval and expected event workload.
