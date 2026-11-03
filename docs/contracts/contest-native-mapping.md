# A10 — DMOJ clock and fixed scoring mapping

Historical A10 evidence: design complete; a bounded native-method probe ran,
without deployment. B11 now deploys/verifies the scoped fixed scorer and private
two-entrant route ([evidence](../../reports/b10-b11-contest-1/README.md)); broader
admission/rejudge enforcement remains later work. Product rules: [contest rules](contest-rules.md).
Selected site: A09 commit `604d60cfd764bc708b04ffd75b715a5398b91f8b`, AGPL v3;
source file hashes and observed checks: [A10 evidence](../../reports/a10-native-1/evidence.json).
The existing converter, package scores and judge pins are unchanged.

## Native records and fixed settings

| Product concept | Existing DMOJ mapping / required setting |
| --- | --- |
| Shared official schedule | `Contest.start_time`, `end_time`; `time_limit=None`. Store aware times; format in viewer timezone. |
| Individual official entry | `ContestParticipation(user, contest, virtual=LIVE=0)`; native uniqueness is `(contest,user,virtual)`. `real_start` records join time, not the official scoring origin. |
| Author testing | `SPECTATE=-1` is the native unranked participation candidate; scoped test/preview path must force it and must not trust requested role/mode. Ranked query selects `virtual=0`. |
| One solved point per problem | `ContestProblem.points=1`, `partial=False`; preserve package case points independently. Additional full-AC guard below is required. |
| No ratings/freeze/pretests | `is_rated=False`, `run_pretests_only=False`, `scoreboard_visibility=SCOREBOARD_VISIBLE`; all official cases must be judged. |
| Stored standings | Reuse `ContestParticipation.score`, integer `cumtime`, `format_data`, `ContestSubmission` and recompute hooks; no second scoring engine/database. |
| Fixed preset | Add a bounded registered format, proposed `format_name='cpjudge_icpc_v1'`, with fixed 1200-second failure penalty; reject alternate settings in all author/API/admin mutation paths. This name is a proposed local addition, not upstream support. |

`format_name='icpc'`, `format_config={'penalty':20}` are a useful native baseline,
but do not implement the agreed preset. Stock ICPC config accepts only `penalty`;
there is no existing configuration switch for failure-code sets, full-AC checks,
per-problem rounding or removal of the final-solve tiebreaker.

## Clock and registration mapping

[`ContestParticipation.start/end_time`](https://github.com/DMOJ/online-judge/blob/604d60cfd764bc708b04ffd75b715a5398b91f8b/judge/models/contest.py#L560)
already give LIVE entrants the shared start/end when `time_limit=None`.
For 10:00–12:00, joining at 10:40 leaves 80 minutes; AC received at 10:50
contributes 3000 seconds, before failure penalties. Setting a per-user duration
would change `start` to `real_start` and is forbidden for this preset.

[`ContestJoin`](https://github.com/DMOJ/online-judge/blob/604d60cfd764bc708b04ffd75b715a5398b91f8b/judge/views/contests.py#L368)
creates entries during a running contest, refuses ordinary pre-start joins and
creates virtual entries after an ended contest. It does not implement separate
pre-registration or the product's late-registration switch. Keep a registration
record/state distinct from current navigation context; D07/D08 must implement
pre-start registration, start/end/capacity locks and no deregistration after start.
Do not treat `ContestLeave`/clearing `Profile.current_contest` as deregistration.
Post-end practice/virtual creation is deferred and must be disabled in the MVP path.

Native `Contest.ended` and participation `ended` use `end_time < now`, allowing
the equality instant. [`ContestMiddleware`](https://github.com/DMOJ/online-judge/blob/604d60cfd764bc708b04ffd75b715a5398b91f8b/judge/middleware.py#L83)
checks current participation once per request; `Profile.update_contest()` can
clear that context, and
[`ProblemSubmit.form_valid`](https://github.com/DMOJ/online-judge/blob/604d60cfd764bc708b04ffd75b715a5398b91f8b/judge/views/problem.py#L694)
does not recheck deadline while creating `Submission`/`ContestSubmission`.
This is insufficient for the required interval **`start <= receipt < end`**.

The official submit endpoint must carry explicit contest/entry/problem identity,
lock/reload the applicable entry and contest rules, obtain fresh server time and
validate schedule, registration, removal and version inside the creation
transaction. Never silently turn an expired official submission into practice
because current-contest middleware cleared the profile context. Define the
persisted submission creation time as the admission receipt and order equal times
by submission primary key; the browser and worker completion clock have no role.
On successful commit, dispatch through the existing judge API; failures need a
recorded infrastructure state, not a contestant failure. Retries keep the original
receipt. Test exact-end and extension/removal races against the real database in
B10/B11/D08; cached `_now` properties are not an atomic admission guard.

## Native scorer differences and bounded changes

Source:
[`ICPCContestFormat.update_participation`](https://github.com/DMOJ/online-judge/blob/604d60cfd764bc708b04ffd75b715a5398b91f8b/judge/contest_format/icpc.py#L46),
[`Submission.update_contest`](https://github.com/DMOJ/online-judge/blob/604d60cfd764bc708b04ffd75b715a5398b91f8b/judge/models/submission.py#L177),
[`ranking queries`](https://github.com/DMOJ/online-judge/blob/604d60cfd764bc708b04ffd75b715a5398b91f8b/judge/views/contests.py#L695).

| Area | Stock behavior | Required preset behavior |
| --- | --- | --- |
| Full acceptance | `update_contest` rounds case ratio to 3 places; `partial=False` rejects only a ratio not equal to full points. ICPC SQL uses maximum stored points without status/result gating. | Credit one only when authoritative attempt is final (`status='D'`), `result='AC'`, `case_total>0` and `case_points==case_total`; no rounded partial credit. Keep package case/group scores. |
| First solve | Minimum timestamp among maximum-point submissions; ordering has no submission ID. | First qualifying full AC in `(receipt, submission.id)` order. |
| Failed attempts | Every non-null result except `IE`, `CE`; `date<=first_time` then count minus one. | Before first AC, count only final `WA`, `TLE`, `MLE`, `RTE`. Exclude pending, CE/IE, `SC`, `AB`, `OLE`, `IR`; preserve native verdicts in details. Same-time later IDs cannot add penalty. |
| Timing | Sums fractional solve seconds; assigns that float to integer `cumtime`. | Floor elapsed whole seconds separately for each solved problem, then sum and add 1200 per prior qualifying failure. Explicit integer computation avoids database conversion deciding rounding. |
| Unsolved/after AC | Unsolved contributes no total penalty; later dated attempts do not affect the first maximum score. | Retain unsolved zero penalty and ignore all attempts after first AC; still show truthful attempt history. |
| Competitive ties | Last solve stored in `tiebreaker`; ranking key includes it; row order also uses submission count. | Set `tiebreaker=0` for preset; competitive rank key is `(score,cumtime)` only. Stable row order by participation ID. Native `ranker` already yields `1,1,3`. |
| Removed/DQ | Native disqualification sets score to -9999 and bans join; does not represent all removal semantics. | Keep submission history; filter DQ from ranked rows and show a DQ designation separately. Access-only removal retains earned ranking unless explicitly disqualified; implement A07 removal state/audit. |

Keep native event-to-`Submission.update_contest()`/participation recompute wiring.
The preset adapter should query authoritative final attempts in stable order,
compute one result per problem and persist native aggregate fields atomically.
Use the native format registry and display hooks for the selected preset; share
the same rank key across HTML, AJAX, exports and finalization. Do not globally
change upstream ICPC semantics for other formats. B11 implements this bounded
extension; A10 only specifies it.

Native [`judge_submission`](https://github.com/DMOJ/online-judge/blob/604d60cfd764bc708b04ffd75b715a5398b91f8b/judge/judgeapi.py#L53)
resets results on rejudge and deletes current case rows;
[`on_grading_end`](https://github.com/DMOJ/online-judge/blob/604d60cfd764bc708b04ffd75b715a5398b91f8b/judge/bridge/judge_handler.py#L355)
calls recomputation. Keep original receipt/source/version and record attempt
history before replacement. A replacement changes the submission's authoritative
result, never adds an extra penalty attempt. While rejudge is pending, mark
standings provisional and treat the attempt as pending; recompute affected entry
at rejudge start/completion. Stale-event/attempt fencing is required in F10/F11;
the native packet must not be assumed to carry a new invented attempt field.

## Concrete expectations and observed probe

Command: `python3 -B reports/a10-native-1/probe.py` — exit **0**.
The script verifies a clean checkout and exact Git bytes, then executes extracted
native method bodies with explicit aggregate/query fixtures, plus the unmodified
pure `ranker`. SQL, ORM persistence and CPJudge scoring implementation did not run.

| Sequence | Contract expectation | Observed native method behavior |
| --- | --- | --- |
| Join 10:40 in 10:00–12:00; AC 10:50 | 80 minutes left; 1 solved, 3000 s | Shared start/end and 3000 s confirmed. |
| WA, TLE, AC at 35:00 | 1 solved, 4500 s (75:00) | 4500 s confirmed. |
| OLE, IR, SC, AB, AC at 35:00 | 1 solved, 2100 s | Stock counts all four: 6900 s. |
| Two ACs at same 35:00 timestamp | First ID solves; 2100 s | Stock counts later same-time AC: 3300 s. |
| ACs at 60.6 s and 120.6 s | 2 solved, 180 s | Stock assigns 181.2 to `cumtime`; no ORM persistence tested. |
| Case ratio 9996/10000, result AC | 0 solved | Native ratio rounding assigns 1 contest point. |
| Full case points but RTE | 0 solved | Native conversion method alone assigns 1; final-result guard needed. This is a constructed consistency fixture, not an observed judge output. |
| Equal 2 solved/3600 s; last solves differ | Shared rank 1,1,3 | Native rank key gives 1,2,3; native ranker with contract key gives 1,1,3. |
| At exact 12:00 deadline | Official submission refused | Native `ended` is false; one microsecond later true. |

Rejudge example for B11/F10: WA 10:10, AC 10:35 initially contributes 3300 s.
Replacing that WA with CE yields 2100 s; replacing the AC with WA yields zero
solved/zero penalty unless another qualifying AC exists. Admission and receipt
remain unchanged. At the historical A10 boundary these were specified examples, without SQL or live
judging. B11 now verifies the registered preset, real worker-to-standings path and
SQL ordering for the scoped fixture; authoritative-replacement calculations use
constructed inputs. Concurrent admission, operational rejudge and stale-event
fencing remain **NOT TESTED**.

## D01–D06 scoped implementation

Native Contest retains the UTC schedule and fixed rules; additive ContestWorkflow
stores the display IANA timezone and provisioned-account policy, and
ContestProblemLabel maps labels to native ordered ContestProblem rows. Drafts use
is_visible=False; publication sets visibility plus published_at atomically and
locks settings. No native field repurposing or Lua label execution. Schedule edits
invalidate draft admissions; author re-selection binds the current accepted probe.
Publication makes a fresh authenticated local bridge challenge, reusing C11's
connected-worker byte/runtime verification; native dispatch repeats its own check.
This separate private channel adds no DMOJ protocol fields. At the D01–D06 boundary, managed registration
was deliberately blocked pending D07. Exact [S,E) checks passed on constructed DB
receipts; concurrency/admission races remain D07/D08. Evidence:
[scoped D01–D06](../../reports/phase-d-d01-d06-1/README.md).

## D07–D09/D11 scoped enforcement

ContestEntry uniquely maps (contest,account) to a retained native participation;
active/withdrawn/removed/DQ state is independent of Profile.current_contest.
Published registration runs until E with late entry enabled; withdrawal requires
server time < S. Native leave only clears navigation. Account/contest locks and
DB uniqueness serialize registration and admission. D11 locks actor and target
accounts in ID order before contest/entry locks; its HTTP path rechecks session
hash/generation after releasing the initial middleware check transaction, avoiding
audit-foreign-key lock inversion. Content conflicts remain permanent and unranked.

ContestReceipt atomically pins explicit contest/entry/version/runtime, payload and
idempotency key to the native Submission.date receipt in [S,E). Retries return the
same admitted submission even after E; a changed payload is rejected. Generic
native POST cannot fall back to practice or another contest after context expiry.
Queued accepted receipts remain valid after removal/end/session changes; new
admission requires current authorization. Native scoring remains authoritative.
Removal keeps rank/score with a marker; DQ excludes rank but preserves score/evidence,
including later native callback recomputation. Only scoped organizers see emails.
Evidence/limits: [D07–D09/D11](../../reports/phase-d-d07-d11-1/README.md).
