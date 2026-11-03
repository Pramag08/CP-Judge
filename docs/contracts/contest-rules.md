# A07 — individual contest rules

Status: **specified; B10/B11 now verify the scoped native private contest and fixed
scoring subset** ([evidence](../../reports/b10-b11-contest-1/README.md)). D07–D09/D11 now pass scoped local registration, atomic admission and removal/DQ
checks ([evidence](../../reports/phase-d-d07-d11-1/README.md)); broader finalization,
operational rejudge and recovery enforcement remain unfinished.
One account, one official individual entry, one fixed ICPC/20-minute preset at
every supported participant count. Teams, groups, ratings, alternate formats,
freeze/reveal and general announcements are deferred. A10 maps these rules to
the selected source; A07 examples below are normative expectations, not test runs.

## Lifecycle and admission

MVP competitions are supervised and in person. D14 problem clarifications are
deferred and removed from required dependencies. No standalone problem archive,
practice, editorials, virtual participation or announcements in MVP navigation.

Persist draft, published/scheduled, cancelled and finalized states; derive
scheduled/running/ended from the server's UTC start S and end E (S < E).
Running means **S <= receipt < E**. Store/display timezone separately; browser
countdowns and worker clocks do not admit submissions. Finalization is explicit
after all admitted official jobs/rejudges finish; pending jobs keep results
provisional. Unresolved infrastructure/jury errors also block finalization until
resolved or covered by an explicit audited incident decision. A cancellation
accepts no further jobs and retains prior evidence.
Pause/resume is unsupported; use documented incident handling/cancellation.
Live extension/problem correction (F13) is deferred, with its safety contract
below retained for future enablement.

MVP eligibility is one policy for active administrator-provisioned accounts,
including college and external participants, subject to scoped removal and
registration rules. Invitation/public-policy selectors are deferred (D04).
Historical private allowlist fixtures/results remain preserved; no access is
changed by this contract update. Network reachability never grants contest
management permissions. Identity follows locally completed C18/C19 in [A06](permissions.md).
Authenticated home shows only eligible published contests (plus an author's own
draft management); registration counts exclude removed entries and unranked tests.
Before start, eligible viewers see schedule/rules but no statements/hidden assets.
Registered active entrants access problems at start; eligible ended-contest viewers
can see published statements/results, subject to source/privacy policy. Removed
entries remain denied even after end. No anonymous private discovery or URL bypass.

| Time/state | Register | Deregister | Official Submit |
| --- | --- | --- | --- |
| Draft/cancelled | No | No self-service change | No |
| Published, registration open, before S | Eligible and below capacity | Yes, preserve audit | No |
| Running, late entry enabled and registration open | Eligible and below capacity | No | Active registered official entrant |
| Running, registration closed/late entry disabled | No | No | Existing active official entrant |
| At/after E | No | No | No; already admitted jobs finish |

Registration window is [Ropen, Rclose), bounded above by E. Default Rclose=E,
late entry enabled; authors may close registration earlier. Setting late entry
false prevents joining at/after S regardless of Rclose. Re-entering the contest
page is allowed for an existing entrant and is not a new registration. A native
“leave contest” action must not deregister an entrant or reset their clock.
Pre-start deregistration permits re-registering while open; removed/DQ entries
cannot self-register again. No extra time or reset penalty on late entry.

Atomic admission checks account/session generation, current eligibility, active
entry, conflict/ranked status, problem version/language, S/E, idempotency key and
capacity where relevant. Serialize on contest/entry records in a consistent order;
sample server time after acquiring the admission lock. Receipt is the durable
server admission timestamp, not a client click, request arrival at a proxy, or
judging completion. Persist receipt + submission ID as the total attempt order.
An accepted idempotent retry returns its original receipt even after E; a new
request after E fails. Pending infrastructure cannot manufacture an earlier receipt.

## Changes, removal and disqualification

Before publication/editing deadlines, authorized authors may edit draft settings.
After S, freeze the scoring preset, eligibility policy, problem versions, language
and limit configuration. Removal and audited restoration are explicit exceptions
for an individual's access. Do not silently rewrite already admitted attempts.
F13 is deferred; if later enabled, an authorized correction publishes an immutable new version with an audit event,
problem clarification and explicit affected-attempt rejudge plan. New attempts
pin the new version; old attempts retain their original version/attempt history.
An audited extension changes E prospectively and updates every server deadline
and visible clock; it does not revive rejected requests or change S/penalty origin.
Finalized results must be explicitly reopened before a correction/rejudge.

| Administrative action | Access/future jobs | Existing attempts and ranking |
| --- | --- | --- |
| Remove entry, recorded reason | Revoke contest read/Run/Submit/rejoin and live channels | Preserve attempts and earned official score; retained standings row marked Removed |
| Disqualify, recorded reason | Same access denial | Preserve attempts; exclude whole entry from ranks; show DQ marker in authorized results |
| Restore, recorded reason | Re-enable eligibility/access only within current rules | Restore retained ranking unless separately DQ/conflicted; no clock reset or retroactive submissions |
| Disable account | Revoke authentication in every contest | Retain history; no automatic DQ or score deletion |

Removal alone is not a score sanction. Explicit DQ recomputes other ranks.
Revocation cannot recall data already viewed/downloaded. Cancel queued custom
runs on removal where possible; accepted official jobs remain evidence and finish
under the recorded rules. Changing an allowlist entry after start must use these
actions rather than indirectly deleting access/history.

## Scoring, penalties and expected examples

Only ranked, admitted official submissions count. Each problem is one solved
point iff its authoritative final result is full AC; native case/package points
remain separate and preserved. A partial score, dependency skip, absent executor,
internal error or incomplete log is not acceptance. Sort each problem's attempts
by receipt then ID, take the first authoritative full AC, and count prior final
WA/TLE/MLE/runtime errors only. CE, queued/running, aborted/infrastructure/jury
errors, OLE/IR/SC/AB and skipped cases add no penalty. Later attempts add none. If no AC, that
problem contributes no penalty. Pending results make standings provisional.

Problem penalty = floor((first AC receipt - S).total_seconds()) + 1200 * failures.
Rank by solved descending, total penalty seconds ascending; equal pairs share
competition ranks 1,1,3. Stable account/entry ID orders tied display rows without
breaking the competitive tie. Rejudge replaces the authoritative result, then
recomputes all affected first-AC/failure/rank calculations, retaining old attempts.
While a replacement is pending, withhold that attempt’s old credit from provisional
standings; do not treat the historical verdict as the current final result.

| Example (S=10:00:00, E=12:00:00) | Expected outcome |
| --- | --- |
| Join 10:45; AC 10:50, no failure | 1 solved, 3000 seconds (50:00); remaining time at join 75 minutes |
| WA 10:05, TLE 10:10, AC 10:35 | 1 solved, 4500 seconds (75:00) |
| CE 10:05, WA 10:10, AC 10:35 | 1 solved, 3300 seconds (55:00) |
| WA only, even with many failures | 0 solved, 0 penalty |
| AC 10:35:00.999; two qualifying failures | 4500 seconds; fractional seconds truncated per problem |
| Receipt 11:59:59.999; judging completes 12:05 | Admitted, may score; results provisional until complete |
| Receipt exactly 12:00:00 | Reject new official submission; no attempt/score |
| Deregister exactly S without any submissions | Reject; author removal remains possible |
| Two last-seat registrations concurrently | Exactly one new active entry; other gets full; unique account entry enforced |
| WA and AC same receipt timestamp, IDs 10 then 11 | One failure counts; reverse IDs means no prior failure |
| Two entrants solve 2 problems for 4500s, third 1 for 100s | Ranks 1,1,3 regardless of last-solve time |
| First AC rejudged WA; next AC at 10:50 | First AC moves to 10:50 and former AC now adds 1200s |
| Remove winner; later disqualify winner | Removal retains winning score/marked row; DQ excludes and recomputes ranks |
| Author previews AC at 10:01 | Unranked test only, no official solved count/penalty |

Later acceptance must exercise these examples through site/bridge/database,
including time/start/end races, late entry, authoritative rejudge and stale events.
No experiment on these examples can substitute for actual integrated judging.

Current managed entry defaults: registration opens on publication, closes at E,
and late entry is enabled. Configurable windows/capacities and restoration UI were
not added by D07–D09/D11. Existing historical private contests retain legacy policy.
