# CPJudge website and judging platform — implementation plan

Version 1.8 • Minimum native website scope reviewed 2 November 2026 • Repository: pramag08/CP-Judge

Current task status and evidence: [PROJECT_STATUS.md](PROJECT_STATUS.md). Read it and
AGENTS.md before work; follow the current documentation workflow in section 19.
MVP task selection and dependency edges: [MVP_DEPENDENCIES.md](MVP_DEPENDENCIES.md).

**Current requested UI override (3 November 2026): COMPLETE — local PASS.** Supplied foobar logo and favicon, `foobar` titles, scoped Contests → Author Contests order, accessible account chevrons, read-only Results links, ended virtual-join rejection and removal of the broken contest Admin tab are implemented in existing templates/assets and the narrow native join route. Staff/participant Chromium, private ranking denial, count preservation and 14 focused tests passed. [Evidence](reports/ui-foobar-virtual-1/README.md). H03 remains pending; no commit or push. This supersedes the plain-text branding status below.

**Local startup review (2 November 2026): COMPLETE — PASS.** B02 now has bounded
bridge/Celery readiness and honest status checks; top-level start gates success
on complete status, including worker/container/native state. A fresh labelled
submission36 AC/103 cases, supported idle stop/start, post-restart login, verdict
persistence and exact-version worker reconnect passed. Retired event service
remained stopped. [Checks and limitations](reports/startup-review-1/README.md).
Next task: previously selected MVP work only on request.

**Current branding/navigation override (3 November 2026): COMPLETE — local PASS.**
Plain-text `Contests-CPJudge` in the existing header slot and site/admin titles
supersedes older Foobar-logo references below. `b01-staff` retains administrator,
author and participant-page access in one session, with no role-mode selector.
Calendar and footer UI-language controls are removed; compiler selection and
upstream attribution remain. [Focused Chromium and preservation checks](reports/navigation-branding-1/README.md).

**Local startup/status repair (2 November 2026): COMPLETE — PASS.** The B03 status
failure was the deliberately protected anonymous `/status/` route, not worker
startup. The health check now uses native worker state and verifies website login
200 plus the expected anonymous 401. Start/status, Chromium email login, and one
labelled real CPP23 submission (AC on 103 stored cases) passed with existing data.
[Exact checks and limitations](reports/startup-status-fix-1/README.md). Next task:
return to previously selected MVP work only on request.

**Current authorization: original 111 MiB Polygon import-capacity task (2 November 2026), locally verified.**
The complete unchanged package passed author upload, conversion, preview, private
publication, exact-version readiness and reference probe, then two participant
browser submissions and standings. [Current evidence](reports/import-capacity-1/README.md).
E09–E15 remains complete at its prior boundary. No F/G work is authorized.
Retain completed A–D evidence. Reuse native DMOJ pages, Ace editor, authenticated
polling and existing custom guards. Custom changes require a demonstrated gap.
Monaco, split layout, new draft synchronization/autosave, custom Run, extra
languages and redesign are deferred. The current header uses plain text.
The local journey is a separate gate from college-server readiness; internet
independence, second workers and fixed 150+/300-request guarantees are not required.
The updated task rows/dependency selection below supersede historical broader
scope statements; historical reports and their acceptance boundaries stay intact.

This is a proposed build specification, not a statement that these features already exist. Preserve the existing Polygon-to-DMOJ converter, pinned dependencies, fixtures, and compatibility evidence. Inspect the actual repository before changing paths or declaring any milestone complete.

The immediate goal is **CPJudge**, a simple individual-contest website with a
DMOJ visual shell with an emphasis on essential actions. The signed-in home is the eligible
contest list, with plain-text Contests-CPJudge at top left and authorized account actions
at top right. Each contest has Problems, My Submissions and
Standings. Authors create/edit contests, import Polygon packages, manage/remove
entrants. D14 problem clarifications are deferred. Every participant owns their submissions, score
and ranking. One fixed scoring preset applies at every supported participant count.
Administrator-provisioned personal email/password login for college and external
participants, one account per canonical email, one active session per account and
scoped permissions are required. No mandatory college ID/email, public signup,
Google login or forced first-login/reset password change. C18 email-only login is active after authorized development-fixture mappings and
complete canonical inventory; C19 has removed the forced-change gate; verified
college-ID behavior remains historical evidence. The header uses plain-text Contests-CPJudge. Teams, groups, special matches, format
selection, announcements, ratings and matchmaking are deferred, not completed.
The later SecureExam desktop client may reuse the website/server.

“Perfect accuracy” cannot be promised by agents or a plan. This plan makes correctness reviewable through explicit rules, small changes, known-result fixtures, integration checks and release gates.

## 0. Audit corrections and buildability verdict

Reviewed 28 October 2026. The architecture is feasible, but the complete implementation is not yet validated. This review inspected the written plan, selected current upstream files and documentation. It did not clone, execute or audit the user's actual CP-Judge repository. The repository-local A01 task establishes that ground truth.

The original 104 tasks and four feasibility additions are a long-term backlog,
not one first release. This revision retains their IDs/status and adds explicit
identity/session tasks C16–C17 and optional Google task C15 and homepage task E17. Deferred rows are not
release prerequisites or completed work. Follow the selected dependencies in
MVP_DEPENDENCIES.md rather than interpreting table position as execution order.
The audit findings below are historical; this revision supersedes their team/group
delivery scope. A01–A05 and A09 evidence remains intact.

| Finding | Correction / required evidence |
| --- | --- |
| The website dependency stack was treated too lightly | Inspected DMOJ website requirements specify Django >=4.2,<5. Django states 4.2 support ended 7 April 2026; its supported Python list ends at 3.12. Do not assume the host's Python 3.14 can run this site. Add A09 before B01.[8][9][10] |
| Pinning an old stack reproduces it but does not maintain it | Evaluate a supported upstream revision, a reviewed maintained fork, or a bounded upgrade to a supported Django stack. A disposable localhost legacy reproduction can help investigate, but it does not pass the deployment gate. Upgrading a version constraint alone is not a verified migration. |
| Manual installation and author upload were conflated | M1 uses one previously converted package installed by an operator and stock site interfaces. The guided author ZIP upload is delivered in C05–C14. |
| Team support looked as small as a format dropdown | The inspected participation model is associated with a user profile. Individual-account team rosters, attribution and aggregation remain a substantial extension to verify; no claim that the model inspection is an exhaustive team-support audit.[11] |
| A late entrant's clock needs an actual upstream mapping | The inspected model distinguishes a common contest clock from per-participant durations. Map the chosen preset explicitly and test late entry; do not assume labels configure it correctly.[11] |
| Versioned problems and worker pools need dispatch design | Verify native problem identifiers, caching and worker selection. A practical candidate is an immutable internal judge problem code per version, with a separate display problem identity. Confirm this against the pinned bridge/judge; do not assume the protocol accepts a new version field. |
| Custom Run integration has not been established | Inspect upstream execution/protocol extension points before implementing E07. Run is a separate bounded untrusted-code path and may require custom work. |
| Bulk tasks appeared to include publication without setup | Add C13's verified probe result, or an equivalent explicit isolated smoke check, to the final publication readiness gate. |
| Several dependency edges were incomplete | Add the result/error checks to the M1 gate; make F07 depend on E12; require completed Run UI for flooding/offline tests. |
| Pilot readiness had too many universal prerequisites | A small private individual pilot can precede teams and second-worker deployment. Only advertise team, multiple-worker, offline and 300-burst capabilities after their corresponding checks pass. |
| Persistent task context was missing | Read PROJECT_STATUS.md and the actual plan before work; complete one requested task and update its evidence/status. Learning happens in a separate ChatGPT conversation. |

No result in this section establishes site/judge compatibility on the user's machine. Captured master-branch source is useful audit evidence; the implementation must resolve and record immutable source commits before choosing its actual stack.

**Starting integration proof:** one operator, two participant accounts, one
ordinary individual contest, one supported C++ problem and one isolated judge
worker. Two accounts are a test fixture, not a special mode or product limit.
Use stock upstream pages for M1; deliver the simplified CPJudge UI in M2. Team,
group and special-match work is outside the MVP.

**Framework decision gate:** before beginning website feature work, record source commit, Python/Django versions, dependency lock, support status, startup/migration results and required local patches. Keep the converter and judge runtime environments separate from the website environment. If no bounded maintainable DMOJ site route is established, stop feature work and record the alternatives and migration costs; do not silently replace the agreed platform.

## 1. Product scope and delivery order

Delivery order (completed historical stages are retained):

1. A–D local foundations, identity/import and author/participant gates: retain
   completed evidence rather than repeat their implementation.
2. Finish essential navigation and targeted native editor/privacy usability gaps.
3. Execute the new combined local H03 browser journey; fix concrete blockers.
4. Inspect/reuse native bounded rejudge/finalization/export; verify missing guards.
5. Separately authorize college-server production/network/restore/recovery and
   representative event-load checks. Internet independence and fixed capacity
   guarantees are optional; no second worker is required.
6. Desktop security, teams/groups and other deferred features remain later work.

Do not make all future features prerequisites for the first usable website. Keep a working deployment at each stage.

Public Codeforces problem URLs are not complete judge packages. The initial import route requires an authorized, complete Polygon package supported by the existing adapter. A URL-only import feature is outside this release.

## 2. Reuse and technical architecture

DMOJ documents contest formats, organizations/access restrictions, fine-grained staff permissions, live submission updates and multiple judging servers. Reuse these where the pinned source and integration tests establish the required behavior. Its website and judge server are separate upstream projects.[1][2]

| Area | Proposed implementation | Required verification |
| --- | --- | --- |
| Website/backend | A maintained DMOJ-derived Django site | Pin a site commit compatible with the existing judge; establish a minimal patch set |
| Database | MariaDB/MySQL, following DMOJ deployment guidance | Pin and test a supported version; exercise restore and migrations |
| Background services | DMOJ bridge, event services and applicable Redis/Celery services | Inspect the pinned deployment; do not assume a new generic task queue replaces the judge bridge |
| Judge workers | Existing pinned DMOJ judge/runtime | Verify compiler availability, isolation and result behavior on every worker |
| Polygon import | Existing strict converter, behind an author import workflow | Add website installation and publication; conversion alone is insufficient |
| Main pages | Customize DMOJ templates and styling for the eligible-contest home and three contest tabs | Plain-text Contests-CPJudge header, scoped profile menu, private eligible list and no deferred feature navigation |
| Editor | Reuse native Ace/source form and language selector | Test enabled languages, account-safe saved code and native submission receipt; add only a bounded file-to-source control if needed |
| Deployment | One college server: website, DB, Redis/background services and isolated judge worker; retain separate coordinator/worker settings | Rehearse laptop-to-server deployment, LAN access, recovery and measured capacity; no second machine required |
| Testing | Existing Python tests plus browser journeys and measured load tests | Pin chosen test tools after checking the repository |

DMOJ's documented site setup uses MariaDB/MySQL and Redis.[3] Retain the installed native editor; Monaco is deferred.

Keep one authoritative website/database and an isolated judge worker on the same college server for the MVP. Additional workers are deferred. Do not introduce Kubernetes, duplicate databases on every laptop or independently running contest sites for the same contest.

### Submission path

Browser → authenticated site endpoint → stored submission → existing DMOJ dispatch/bridge → compatible worker → case results → stored judge attempt → server-side score calculation → participant page and standings.

The converter is used when importing or revising a problem. It must not rerun conversion for every submission. The existing CLI compatibility runner remains a regression tool; it is not the production request handler.

The database, judge protocol and pinned implementation must be inspected before finalizing retry behavior. Add integration code for gaps; do not replace working upstream scheduling simply to make the architecture appear cleaner.

Phase A normative contracts: [permissions/sessions](docs/contracts/permissions.md),
[contest rules](docs/contracts/contest-rules.md). These supersede older broad role
summaries where they differ. Native [clock/scoring](docs/contracts/contest-native-mapping.md),
[version/dispatch](docs/contracts/problem-version-dispatch.md) and
[custom Run](docs/contracts/custom-input-run.md) designs are complete with evidence
in the A10–A12 rows. Phase A closed at that boundary; B01 is now complete for
the local stock website/database. B02 service readiness and B03 authenticated
worker/executor registration and B04/B05 private problem installation are complete;
B06 rendering and B07 real browser judging are complete for one private CPP23
reference (submission1/103 AC). B08/B09 WA/CE/RTE/TLE probes pass (submissions2–5).
B10/B11 pass the private two-entrant standings route; B12 passes supported restart
persistence and continued judging. Phase B / M1 is COMPLETE for these scoped gates;
broader lifecycle, interrupted judging recovery and production remain untested.

## 3. Profile roles and scoped permissions

The top-right profile menu identifies Participant, Author or Admin and exposes
only views/actions the account is authorized to use. Participant is the default;
author/admin views require actual grants. Switching views never changes identity
or grants permission. Do not add a participant-format selector.

Internally distinguish platform ownership, organization management, contest ownership, editing, reviewing and participation. These can be permission bundles rather than extra visible modes.

| Action | Participant | Authorized contest author | Administrator/operator |
| --- | --- | --- | --- |
| View accessible contests and problems | Eligible scope | Assigned scope | Contest scope required |
| Register and submit under contest rules | Yes | Yes, with conflict rules below | Yes, with conflict rules below |
| Create a contest | Only after an author grant | Yes | Yes |
| Edit a contest or its problems | No | Assigned contests/problems only | Explicit edit scope |
| View participant roster emails | Own email only | Assigned contest, with explicit roster permission | Only with authorized contest-roster scope |
| Invite/remove/disqualify entrants | No | Assigned contest, according to policy | Explicit entrant-management scope |
| Grant contest editor/reviewer permissions (optional follow-up) | No | Within permitted delegation scope if enabled | Explicit delegation scope; no new grant UI required for MVP |
| Grant platform administrator privileges | No | No | Platform owner only |
| Create/reset/disable accounts; grant author | No | No | Account administration scope |
| Review submitted source | Own source | Explicit contest source-review grant | Source-review scope; account admin alone grants none |
| Change judge secrets or machine configuration | No | No | Trusted infrastructure operator only |
| View hidden tests/reference solutions | No | Only an explicit problem/jury permission | Explicit jury/operational need; account admin alone grants none |
| Review audit records | Own relevant activity where appropriate | Assigned scope | Explicit audit scope |

Every protected page, API endpoint, export and live-update channel must enforce
scope server-side. Test independent contests and unauthorized/removed accounts.
An Admin label does not create an unscoped email directory. Participants' emails
must not appear in another participant's HTML, JSON, standings, events or exports.

Authors retain participant capabilities in unrelated contests. Owners, editors,
source/jury reviewers, importers and testers are unranked throughout their own
contest, including preview. Revoking a grant does not erase the conflict flag.

Record who changed permissions, imported problems, modified rules, rejudged, extended a contest or disqualified a participant. Prevent a contest author from promoting themselves to site administrator.

## 4. Provisioned accounts, recovery and private rosters

Authorized account administrators provision personal email/password accounts for
college and external participants. No mandatory college ID, college email, Google
login or public signup. One account per canonical email must be database-enforced.
Normalize by trimming outer whitespace, validating the supported email syntax and
lowercasing the entire address under the documented case-insensitive login policy;
reject unsupported syntax explicitly. Do not strip Gmail dots or +suffixes.
See [A06](docs/contracts/permissions.md) for migration/conflict/rollback requirements.

No forced password change on first login or after organizer reset. Participants
contact organizers outside the application for recovery; no automated email delivery
or reset-token service is required. An authorized account administrator verifies the
requester outside the app, resets using Django secure password hashing, revokes all
sessions and records the actor/target/time/outcome without logging credentials.

The basic authorized contest roster shows names/handles, private emails,
registration time and participation status with pagination. Advanced filters,
roster CSV export and additional editor/reviewer grant controls are deferred;
retain implemented scopes and restrictions. Standings never expose emails.
Account administration alone grants no contest-source or hidden-test access.

Reuse one-active-session enforcement: a new login invalidates old sessions, while
tabs sharing the same session remain valid. This is not physical-device binding.
Password reset/disable revokes all sessions. C17's verified implementation remains;
C18 email-only cutover passes; C19 removed the forced-change gate, with
session/recovery regressions required. Preserve existing accounts, password hashes,
IDs, submissions and audit history; never guess missing emails or merge conflicts.

Serve editor/scripts/fonts/math assets locally. Validate time against the server.
Account disabling and scoped contest removal remain distinct and preserve records.
Approved campus reachability is a separate G14 server check; internet independence is optional. Remote access needs
separately approved VPN/public deployment, not merely account credentials.

## 5. One individual contest and one scoring preset

One ordinary individual contest system serves every supported participant count.
Two entrants, twenty entrants and a larger tested cohort use the same models,
routes, registration rules and scorer. Capacity limits are operational limits,
not participant formats. No UI field, API requirement or branch selects 1v1,
2v2, XvX, team or group competition. The MVP uses one active provisioned-account eligibility policy with scoped
participant removal; invitation/public-policy selectors are deferred. Keep upstream organization/team-related internals where they
exist; hiding features is not an instruction to delete backend models.

The only MVP scoring preset is **CPJudge Individual ICPC (20-minute penalty)**:

- More solved problems ranks higher.
- Equal solved counts are ordered by lower total penalty.
- Every problem contributes one solved point only on a full accepted result; no
  partial contest credit or alternate scoring selector. Native case/package points
  remain preserved independently of the contest's solved count.
- For each solved problem, penalty is elapsed whole seconds from the common
  contest start to the first accepted submission, plus 1200 seconds per qualifying
  prior failed attempt. Truncate elapsed fractional seconds per problem; display
  minutes/seconds without changing the ranking value.
- Count final WA, TLE, MLE and runtime-error submissions as qualifying failures;
  exclude CE, infrastructure/jury errors, queued/unjudged attempts and dependency
  skip records. Rejudge uses the authoritative replacement result.
- An unsolved problem contributes no penalty.
- Attempts after the first acceptance do not add penalty.
- Equal solved and penalty totals share a rank; use a stable display order without inventing a hidden competitive tiebreaker.
- Count qualifying submissions by server receipt time and a stable secondary ordering. Judging completion time never determines solving time.

For example, first AC at 35:00 after two qualifying failures contributes 75:00.
Two participants with the same solved count and penalty share a rank (1, 1, 3).
Only official eligible individual submissions count; author previews are unranked.

Reuse native `Contest`, `ContestParticipation`, `ContestProblem`,
`ContestSubmission` and the contest-format registry. Starting mapping on A09's
pinned source: `Contest.time_limit=None`, `is_rated=False`, contest problem
`points=1`, `partial=False`, ICPC format configuration `penalty=20`. Freeze this
preset in the author UI and validate it server-side; a crafted request must not
enable hidden formats or alternate scoring. Existing DMOJ score storage,
dispatch and recomputation remain authoritative.

Source inspected: `judge/contest_format/icpc.py:ICPCContestFormat.update_participation()`,
`judge/views/contests.py:contest_ranking_list()/get_contest_ranking_list()`, and
`judge/models/contest.py`. Stock ICPC awards native points, has a last-solve
tiebreaker and uses broader failure filtering; simply setting `format_name='icpc'`
does **not** implement every rule above. A10 specifies the bounded registered
`cpjudge_icpc_v1` extension; B11 must implement/verify full-AC credit, failures,
elapsed-second rounding, ties and rejudges. Do not rewrite the contest engine or
silently adopt differing upstream semantics. B11 now implements this bounded extension; [measured evidence](reports/b10-b11-contest-1/README.md). Broader author preset freezing and lifecycle/rejudge enforcement remain later tasks.

Alternate/partial contest scoring is deferred. Polygon testcase/scoring groups
are technical package data, distinct from deferred participant groups; preserve
the existing converter, fixtures and A03 evidence for them.

## 6. Registration and a common contest clock

### Registration rules

| Contest state | Register | Deregister | Submit |
| --- | --- | --- | --- |
| Scheduled; registration open | Yes, if eligible and space exists | Yes | No |
| Running; late registration enabled | Yes, subject to eligibility/capacity | No | Yes after joining |
| Running; registration closed | No | No | Existing eligible entrants only |
| Ended | No official registration | No | No; practice/virtual participation deferred |
| Cancelled | No | No | No official submissions |

Default for ordinary contests: allow late registration until the contest ends, unless the author disables it. Late entrants share the original start/end times; they receive no additional time and penalties count from the official start.

Deregistration is blocked once the contest begins even if the entrant has not submitted. An author may remove or disqualify someone with a recorded reason; this is an administrative action, not participant deregistration.

Use a server-side transaction/lock or equivalent database constraint to resolve registration/start/capacity races. Browser button disabling is insufficient.

One official participation belongs to one individual account. Keep native
uniqueness constraints and test concurrent joins/submissions, including contests
with 1, 2 and more entrants. Never pool users' submissions or scores.
Removed entrants lose contest access and future submission permission immediately;
invalidate contest-scoped access/channels and prevent self-rejoining while removed.
Preserve submissions and the removal reason. Any exclusion of existing results
must be explicit/audited through the removal/disqualification policy, with the
standings recomputed; do not silently delete attempts or repurpose account disabling.
Team invitations, shared entries, roster locking and match readiness are deferred
with F01–F07; no team-specific rules block ordinary registration.

## 7. Author experience

Use a guided dashboard instead of requiring routine authors to navigate every underlying Django administration screen.

Author controls are scoped links/forms reached through the profile/contest actions:
contest create/edit, Problems/import, Entrants, permitted
Submissions/Standings, Settings and Activity. Clarifications remain deferred. Keep these out of participant
navigation unless authorized. No Teams, Groups or Announcements area in the MVP.

### Contest creation

1. Enter title/description; use the single provisioned-account eligibility policy.
2. Set timezone, start/end, registration window and late-entry policy.
3. Use the single ordinary individual participation model; no format/team-size field.
4. Show the fixed scoring preset and its exact rules; no scoring-format selector.
5. Add/import problems and order labels A, B, C and so on.
6. Choose tested languages and feedback; use live standings with no freeze selector.
7. Preview as a participant.
8. Run the publication checks and schedule/publish.

MVP eligibility: active provisioned accounts, subject to scoped removal and
registration rules. Invitation/public-policy selectors and group visibility are
deferred; preserve historical private allowlist fixtures and implemented checks. An unlisted link is not an authorization
mechanism; the home list, direct URLs and every action must enforce eligibility.

### Management actions

Provide editing, basic entrant roster/removal, authorized
submission inspection, bounded rejudge, final results export and protected basic
queue/worker health. Invitation selectors, advanced filters, roster CSV, extra
editor/reviewer grants and clone/archive are deferred if unimplemented. D14 clarifications and general announcements are deferred.

Separate “hide the public roster,” “hide standings,” “remove an entrant,” and “disqualify an entrant.” These have different consequences. Disqualification preserves submissions and explains exclusion from ranking.

Before start, allow broad edits within the fixed preset. After start, protect
scoring rules and problem versions. Live contest extension/problem correction is deferred (F13). If implemented
later, require immutable versions, audit, a rejudge plan, clarification and
server-clock consistency; retain any existing behavior and its evidence.

Finalization waits for accepted-before-deadline submissions to finish judging. Mark standings provisional while jobs or rejudges remain. Publishing final results should be an explicit action.

Contest suspension/pause and resumption affect clocks, pending work and penalties; implement only with a specified state machine and tests. The first release uses documented incident handling or cancellation; live extension is deferred.

## 8. Polygon import, statements and problem versions

The author uploads one Polygon ZIP at a time, then attaches verified imports to
a contest. Multi-ZIP selection (C14) is deferred; preserve its backlog history.

The import pipeline is:

Upload privately → validate archive → run the existing strict converter → show a compatibility report → render a safe preview → stage judge data → run approved smoke checks on an isolated worker → install website metadata/assets → publish a version.

Required controls:

- Enforce compressed/uncompressed size, file count and extraction limits.
- Reject path traversal, symlink escapes, ambiguous roots and unsupported package metadata.
- Preserve test order, test-to-display mapping, checker standard, limits, samples and supported group semantics.
- Do not run arbitrary generators, validators or package scripts during web upload.
- Native checker/reference execution, if requested, occurs only on an isolated worker.
- Treat HTML/TeX/assets as untrusted. Sanitize supported statement HTML or render a safe representation; strip scripts, event handlers and unwanted external loads.
- Keep raw originals private. Serve published assets through controlled routes with appropriate content types.
- Show unsupported features as actionable errors, never silently downgrade scoring, C++ standard or checker semantics.
- Record package hash, converter pin, problem version and verification status.
- Make publication atomic: no visible problem with missing tests, unsupported compiler or half-written website metadata.
- When an import fails, existing published versions remain usable.
- Pin every submission to the problem version and relevant contest rules used for that attempt.
- Deploy the same version/hash to compatible workers before scheduling it there.
- Never mutate hidden test files in place during an active contest.
- Support rollback to an earlier version with explicit handling of affected submissions.

Preserved statement files are not automatically website rendering support. Installing and displaying the real supplied package is a separate acceptance test.

The original **111 MiB ZIP is now locally verified** under measured, finite limits:
128 MiB compressed upload plus 64 KiB multipart overhead, 1024 entries, 128 MiB
per member, 320 MiB total expanded and ratio 100. Private-disk upload, bounded
conversion, staging-space checks and the full original author-to-participant
browser/judge journey passed. [Import-capacity summary](reports/import-capacity-1/README.md).
This package-specific proof does not complete broader H03 or operational/load gates.

| Separate task | Status | Evidence |
| --- | --- | --- |
| Original Polygon ZIP import capacity | COMPLETE — local full-package upload, conversion, preview, publication, readiness, reference probe, participant AC/WA and standings verified; no production or load claim | [Measured limits, focused checks and browser results](reports/import-capacity-1/README.md) |

## 9. Participant interface and editor

Approved visual direction: [DMOJ template adaptation](docs/contracts/ui-direction.md).
Keep horizontal navigation, centered content, compact tables, sidebar styling
and the footer. Adapt existing templates; no separate frontend/replacement shell.
The current header uses plain-text Contests-CPJudge in the existing logo slot.

The signed-in **homepage is only the eligible contest list and essential
navigation**. Header: plain-text Contests-CPJudge home link at top left, account and
authorized author/admin actions at top right. No news feed, ratings,
announcements, global problem catalogue, participant-format picker or group/team
navigation. Signed-out users get personal email/password sign-in (C18/C19 locally complete) and then the eligible list.
Show only contests the current account may discover/join/view, with concise
title, schedule/status and entry action; registration/open-seat status must be
truthful. Show a useful empty state. The header brand is exactly Contests-CPJudge.

Contest pages have exactly three primary tabs: **Problems**, **My Submissions**
and **Standings**. Problems shows the title/common clock, essential rules/link,
problem list and own progress. D14 clarifications are deferred for supervised,
in-person competitions. No standalone problem archive/problemset, practice,
editorials, virtual participation or announcements in MVP navigation. Author
management links remain scoped controls rather than extra participant tabs.

Reuse native problem pages and the separate native submission page with Ace,
source textarea, validated language selector, compilation diagnostics, cases,
paginated own submissions and standings. Keep current readable styling and
server-side receipt/idempotency/deadline guards. Small template links/tabs are
sufficient; no split workspace or replacement editor is required.

The inspected submit form has no file chooser. Verify the complete widget path
before adding a bounded local source-file loader into the native source field;
retain the same CSRF-protected submit endpoint, source limits and language checks.
Native Ctrl-S storage uses only a language key. Isolate retained saved code by
account/contest/problem/language so a shared browser cannot restore another
account's source. This is a narrow privacy fix, not a new draft service.

Keep authenticated polling and existing native refresh behavior. Test source and
case visibility on direct URLs and polls, retry receipts, removal, expired
sessions, keyboard use, narrow view and editor failure. Add CSS or fallback code
only for a reproduced blocker. Monaco, split layout, custom draft synchronization,
new autosave/offline infrastructure, custom-input Run and extra languages are
deferred. Existing C13 solution probes and D13 unranked author tests remain required
and working; they are distinct from a participant custom-input Run service.

### Theme interpretation

The phrase “night and dark” is ambiguous. Proposed default: a Light theme and a Dark/Night theme, with optional higher-contrast variants later. If two dark palettes were intended, keep the theme-token system extensible.

Use consistent contrast for statements, controls, tables and code. Proposed acceptance targets: ordinary text contrast at least 4.5:1, visible keyboard focus, 200% zoom without losing core actions, and verdict labels/icons in addition to color. Test actual color pairs instead of describing a palette as “easy on the eyes” without evidence.

Respect the OS preference initially and remember the user's override. Internet access is allowed; public-internet independence is optional. Preserve working local assets.

## 10. Verdicts, feedback and standings

Store the native judge result and present a stable user-facing mapping. Possible outcomes include queued, compiling, running, AC, WA, TLE, MLE, runtime error, compilation error and internal/jury error, according to the actual executor/protocol.

A participant can see “Wrong answer on test 17” when the judge supplies that case result and contest policy permits it. Preserve the Polygon-to-installed-case mapping so numbers are meaningful.

Do not invent results for skipped or unexecuted tests. With early termination, explain that later tests were not run. With grouped scoring, distinguish failed groups, earned points and dependency skips.

Recommended feedback policies:

| Information | During a normal contest | Author/jury |
| --- | --- | --- |
| Overall verdict and total score | Visible | Visible |
| Failed test number, executed-case status, time/memory | Configurable; enabled by default where available | Visible |
| Compilation diagnostics | Own submission, sanitized | Visible |
| Hidden test input/expected output | Hidden | Explicitly permitted reviewers |
| Checker diagnostic text | Filtered or hidden if it may leak answers | Raw detail in restricted diagnostics |
| Other contestants' source | Hidden until release policy allows | Authorized reviewers |
| Rejudge history | Current result plus meaningful status | Full recorded attempts |

Never expose hidden data through JSON, exports, logs or event streams just because the main page hides it.

Standings show individual rank, handle, solved count, penalty, per-problem
result/attempt count and provisional/final status for the one fixed preset.
Each participant's submissions, score and ranking are independent. No shared
team rows, group ranks or rating changes. Never include participant emails.

Add filters and pagination. Preserve the viewer's scroll position during updates. Use polling as a fallback when live updates reconnect.

Score computation belongs on the server. Store enough source events and versioned results to recompute standings. Rejudge updates must not double-award points; late duplicate events must not overwrite a newer authoritative attempt.

The MVP uses live standings with no freeze selector. Optional freeze/reveal (F12)
is deferred; if later enabled, all public pages, APIs and events must respect its
cutoff. Provisional/final state and privacy remain required now.

Virtual/practice attempts never change official standings.

## 11. Logical records and contracts

Reuse DMOJ's existing models and protocol first. These are logical records to map onto upstream structures, not instructions to create a duplicate table for every noun:

User/profile and canonical email (retain legacy IDs); active-session policy; scoped role grant;
problem and immutable version; import job/findings; contest and fixed rules
version; contest-problem assignment; individual participation; submission; judge
attempt; case/scoring-group result; scoped clarification; audit event; worker and
capability/version inventory. Upstream organization/group/team/rating structures
may remain internally, but require no MVP workflows, new shared-entry model or
general announcement records.

Document contracts before parallel implementation:

- Contest lifecycle and registration transitions.
- Permission checks and scope identifiers.
- Individual participation/submitter ownership and removal effects.
- Canonical-email uniqueness, no forced first-login/reset change, verified organizer
  recovery and preserved single-active-session policy (C18/C19 locally complete).
- Import status and publication readiness.
- Submission create/retry response.
- Native-to-display verdict mapping and case numbering.
- Scoring inputs and rejudge replacement rules.
- Worker health/capability/problem-version readiness.
- Custom-run request/result.
- Frontend event payloads and reconnect behavior.

Browser clients are not authoritative for identity, eligibility, score, time
limits, contest clock, session authorization or result generation.

## 12. Single college server and measured operation

One college server hosts the website, authoritative DB, Redis/background services
and an isolated authenticated judge worker. Retain separate coordinator/worker
configuration and pinned images for future flexibility; a second laptop or
heterogeneous/distributed pool is not required. Workers need assigned private
problem data, not the full account database or every application secret.

Preserve judge isolation, unique revocable worker credentials, protected bridge
connectivity, private problem storage, exact-version/hash readiness and immutable
attempt/result handling. Keep DB/cache/internal ports private. Participant-owned
machines are not trusted workers. Protect links on untrusted networks.

Participants need network reachability to the server and provisioned account
login. Campus routes, production configuration and any remote/public exposure
require separate deployment work; do not change host-wide networking for this
local task. Internet access is allowed. Public-internet independence is optional,
not a release prerequisite.

College-server work is a separate checklist: production settings and supported
pins, reachable approved campus networks, fresh isolated backup/restore, worker
interruption/recovery and representative measured event load. Choose the workload
from the actual event; there is no fixed 150+ active-user or 300-request guarantee.
No distributed pool or second laptop is required. Custom Run contention (G12)
is deferred with custom Run. Do not perform deployment/load/recovery tasks merely
to close the local browser journey. G13 → G15 → G14 retains safe restore before
staging and actual campus reachability afterward; G16 records operator procedures.

### Fairness and worker failure

Different CPUs can produce different TLE behavior. An identical container does not make their execution speed identical. For official contests, prefer a homogeneous judge pool, or route a contest to a calibrated approved worker class. Do not assume a simple CPU speed multiplier makes arbitrary problems fair.

Test worker disappearance during compilation and execution, bridge reconnects and duplicate completion events. Retry infrastructure failures as new attempts; never convert a disconnected worker into a contestant WA or TLE. Apply the correct authoritative attempt once.

Worker health checks should prevent new assignment to incompatible/unhealthy machines. A worker must not be considered ready until required runtime and problem hashes are verified.

More workers do not make the central site highly available. Document coordinator downtime, restore and rescheduling procedures.

## 13. Repository layout and maintainability

The target organization below is illustrative. Inspect current paths and preserve the existing pipeline first; reorganizing working code is not the first milestone.

| Proposed path | Responsibility |
| --- | --- |
| AGENTS.md | Task scope, invariants, commands and evidence requirements for coding agents |
| PROJECT_STATUS.md | Concise current architecture, task status, commands, results, decisions and unresolved facts |
| docs/product.md | Approved roles, contest behavior and UI scope |
| docs/architecture.md | Services, data ownership and trust boundaries |
| docs/contracts/ | API/event, scoring, import and lifecycle specifications |
| docs/decisions/ | Short records of material architecture decisions |
| docs/tasks/ | One numbered task specification per small change |
| docs/runbooks/ | Setup, adding workers, incidents, backup and restore |
| apps/site/ | DMOJ-derived site with preserved upstream structure and provenance |
| apps/site/secureexam/ | New project-specific Django modules where compatible |
| apps/site/templates/ | Customized participant and author templates |
| apps/site/static/ | Locally served built assets |
| frontend/editor/ | DEFERRED proposal; reuse native Ace/templates in the actual site tree |
| frontend/theme/ | Shared design tokens, theme styles and accessibility behavior |
| packages/polygon_import/ | Existing adapter wrapped for site imports, when safely extracted |
| integrations/judge/ | Thin compatibility/installation helpers; preserve DMOJ transport |
| deploy/coordinator/ | Site/database/bridge/event deployment configuration |
| deploy/worker/ | Pinned worker build/configuration and enrollment instructions |
| scripts/ | Setup, smoke checks, package installation and release helpers |
| tests/contracts/ | Permission, lifecycle and scoring contract checks |
| tests/integration/ | Import, site, bridge and actual judge integration |
| tests/browser/ | Participant and author journeys |
| tests/load/ | Reproducible burst/sustained workload definitions |
| reports/ | Measured results, limits and known failures |
| local-packages/ | Private ignored Polygon inputs |
| build/ | Ignored generated output |

Keep the converter's current tools/tests paths until a move provides a concrete benefit and passes regression checks. Avoid duplicate implementations during transition.

Record the upstream site commit and local patches so updates remain possible. Choose and document one fork/subtree/submodule strategy before importing source. Do not copy upstream code without provenance.

Maintain dependency/image pins and THIRD_PARTY notices. DMOJ identifies its projects as AGPL-3.0; preserve upstream licensing and include the applicable source distribution/compliance work in release preparation.[1][2]

Use cohesive modules with small responsibilities. File count is not an architectural goal. Extract services only when deployment or ownership needs justify them.

## 14. Small implementation tasks

The earlier2026-10-30 scope consolidation was documentation only; its historical
milestones and reports remain unchanged. Subsequent runtime tasks C11/C12/C13/C19
are locally complete. C18 email-only cutover now passes after explicit organizer-assigned development
fixture addresses, with no mailbox/real-identity verification claim. Phase C is
COMPLETE for all retained local gates ([closure](reports/phase-c-c18-cutover-1/README.md)). The integrated same-version import→probe→official
submission→standings check now passes for one private package/runtime
([evidence](reports/phase-c-integrated-1/README.md)). [Current bundle](reports/phase-c-c13-identity-1/README.md);
C11/C12 retain their separate evidence rows. No general Phase D authorization; only the minimum private admission needed for this requested integrated acceptance was added.

Each row is a separate reviewable task. A task is done only when its stated check passes. If it still spans unrelated changes, split it again before assignment. Dependencies refer to task IDs; tasks without explicit dependencies follow the preceding baseline work.
The explicit MVP selection is in MVP_DEPENDENCIES.md. DEFERRED means outside the
MVP, not completed. Completed baseline evidence is historical and unchanged;
Phase A contracts specify behavior; only rows with evidence are complete and no
Phase B feature is implemented by these specifications.

### A. Baseline and decisions

A01 repository orientation is complete. Its useful map, data-flow, ownership and
evidence facts are consolidated in [PROJECT_STATUS.md](PROJECT_STATUS.md).

| ID | Task | Depends on | Acceptance evidence |
| --- | --- | --- | --- |
| A01 | Inspect repository, AGENTS files, current branches and reports | — | COMPLETE — inventory and retained facts in PROJECT_STATUS.md; historical judging evidence remains separate |
| A02 | Reproduce converter regression tests without changing behavior | A01 | COMPLETE — PASS: 6 tests, 4 conversions/preservation checks; [commands and evidence](reports/a02-converter-1/README.md); judging NOT TESTED |
| A03 | Reproduce the existing isolated judge milestone where available | A01 | COMPLETE — PASS: 18 probes, 454 verdict/score assertions, exit 0; [independent review and evidence](reports/a03-judge-1/README.md) |
| A04 | Pin a candidate DMOJ site revision and runtime requirements | A01 | COMPLETE — [source pin, support/environment audit and A09 gate](reports/a04-site-foundation-1/README.md); website setup NOT TESTED |
| A05 | Map requested features to upstream/custom/unknown | A04 | COMPLETE — [20-feature source map and checks](reports/a05-feature-map-1/README.md); no website implementation/runtime compatibility claim |
| A06 | Record participant/author/admin scope, email privacy and participation-conflict rules | A05 | COMPLETE — [Permissions/identity/session contract](docs/contracts/permissions.md); Specified scope, canonical IDs, private email/source/tests, unranked conflicts and single-active-session generation policy; enforcement NOT TESTED; [audit](reports/phase-a-close-1/checks-A06.json) |
| A07 | Record individual registration, common clock and fixed preset boundaries | A05 | COMPLETE — [Contest lifecycle and fixed rules](docs/contracts/contest-rules.md); Specified registration, [S,E) receipt admission, late entry, removal vs DQ, penalties/ties and expected examples; enforcement NOT TESTED; [audit](reports/phase-a-close-1/checks-A07.json) |
| A08 | Write task template, AGENTS guidance and dependency commands | A02,A06,A07 | COMPLETE — [Project instructions/resume workflow](AGENTS.md); Commands, evidence distinctions, task ownership and resume workflow documented; documentation audit only; [audit](reports/phase-a-close-1/checks-A08.json) |
| A09 | Establish a maintainable website dependency stack | A04 | COMPLETE — PASS for [supported-stack startup](reports/a09-site-1/README.md): official 604d60cf, Python 3.12.16/Django 5.2.18/MariaDB 11.4.13, installation/migrations/79 tests/login/assets/restore verified; metadata-drift diagnostic failed (no DDL), warnings retained; Phase B site/judge compatibility NOT TESTED |
| A10 | Map common-clock and the one fixed preset to native site settings | A09,A07 | COMPLETE — [Native scoring/clock mapping](reports/a10-native-1/README.md); Source mapping and isolated native-method probes PASS; common late-entry clock verified; scoring/deadline adaptations specified; SQL/site integration NOT TESTED; [audit](reports/phase-a-close-1/checks-A10.json) |
| A11 | Investigate immutable problem-version identifiers and compatible-worker dispatch | A09,A03 | COMPLETE — [Immutable versions/compatible dispatch](reports/a11-dispatch-1/README.md); Source/path/cache and 6 native selection checks PASS; immutable native codes, external readiness receipts and attempt mapping specified; live routing NOT TESTED; [audit](reports/phase-a-close-1/checks-A11.json) |
| A12 | Investigate custom-input run execution and protocol integration | A09,A03 | COMPLETE — [Custom-input Run route](reports/a12-run-1/README.md); Source-grounded separate executor adapter, isolation/limits/quotas/result contract specified; actual custom execution NOT TESTED; [audit](reports/phase-a-close-1/checks-A12.json) |

### B. Prove the website-to-judge path

**COMPLETE — PASS: B01–B12 / M1 scoped local acceptance.** B12 proves graceful
completed-result persistence and continued judging; interrupted-job recovery is
untested. [Final Phase B evidence](reports/b12-restart-1/README.md). Phase C authorized; implementation in progress.

| ID | Task | Depends on | Acceptance evidence |
| --- | --- | --- | --- |
| B01 | Bring up the pinned site and database locally | A09 | COMPLETE — PASS: pinned local website/MariaDB/Redis, additive 0153 + callable timezone fix, 202 real migrations and clean consistency, dependency/static checks, 9 actual Chromium auth/admin journeys and stop/start; [setup/results/review](reports/b01-site-1/README.md); warnings/4 scoped JS errors retained; website-to-judge NOT TESTED; bounded [follow-up](reports/b01-followup-1/README.md) COMPLETE — admin/local math/static fixes, password-preserving verification/explicit reset and approved template direction; old B01 evidence preserved |
| B02 | Bring up bridge/event/background services needed by that site | B01 | COMPLETE — PASS, independent review PASS; [real services/evidence](reports/b02-services-1/README.md): native task/event/bridge probes, restart and browser/login smokes; [historical status reconciliation](reports/b02-status-1/README.md): observed stopped before B03 restarted services; no worker enrollment/judging during B02; CORS polling/replay limits retained |
| B03 | Connect the known judge worker to the site | B02,A03 | COMPLETE — PASS; [native authenticated worker/executor evidence and independent review](reports/b03-worker-1/README.md): pinned image/GCC16.2.0, CPP11/14/17/20/23 self-tests and real capabilities, native online/offline/reconnect and full lifecycle, sandbox socket/config denials, existing data/metadata/pins preserved; website judging NOT TESTED |
| B04 | Define problem-version metadata and installation mapping | A02,A11,B01 | COMPLETE — PASS for [source-grounded mapping](reports/b04-installation-1/README.md): opaque immutable native revision/full manifest, 2s/262144KiB ORM→request limits, CPP23 bridged/testlib, 103 ordered cases/sample/assets/scoring; no submission sent |
| B05 | Install one already-converted real problem into the site | B03,B04 | COMPLETE — PASS; [private installation/verification/review](reports/b05-problem-1/README.md): revision1 native pv000000000000000001, 103 ordered source/worker pairs, checker/header/sample/15 assets, CPP23/2s/262144KiB, safe repeat and collision tests, actual worker advertisement,696 HTTP denials, existing data/config preserved with documented access-timestamp precision; judging NOT TESTED |
| B06 | Render its statement, assets and samples safely | B05 | COMPLETE — PASS; [real Chromium/native statement evidence](reports/b06-statement-1/README.md): strict receipt-bound HTML/scoped CSS/TeX,30 exact local MathJax expressions, constraints/samples, restricted participant grant,219 private-data denials; immutable worker bytes/limits preserved; no submission |
| B07 | Submit an accepted probe from a participant account | B06 | COMPLETE — PASS, independent review PASS; [actual native browser→worker evidence](reports/b07-submission-1/README.md): submission1 CPP23, observed2s/262144KiB,103 AC1/1 cases, matching native worker/callback/SQL/browser score103/103;3 compiler warnings retained; [final audit exit0](reports/b07-submission-1/evidence-audit.json); standings untested |
| B08 | Submit wrong-answer and compilation-error probes | B07 | COMPLETE — PASS; submissions2 WA (55 WA/48 AC),3 CE (zero executed); worker/callback/SQL/browser agree; [results/commands](reports/b08-b09-probes-1/README.md) |
| B09 | Verify runtime/time-limit and available case-detail propagation | B07 | COMPLETE — PASS; submissions4 RTE/5 TLE each103 executed cases; worker/callback/SQL/browser positions/status/points agree; zero SC; unchanged2s/262144KiB and sandbox/data preserved; [results/commands/limitations](reports/b08-b09-probes-1/README.md); precise timing parity untested; stopped before B10 |
| B10 | Put the problem in an ordinary contest using two test accounts | B08,A06,A07 | COMPLETE — PASS; private native contest b10b11local1,2 temporary ordinary entrants; real browser access denials/join/problem visibility, separate WA submissions6/7 and common late-entry clock; [evidence](reports/b10-b11-contest-1/README.md) |
| B11 | Compare standings with a hand-calculated submission sequence | B10,B09,A10 | COMPLETE — PASS; native cpjudge_icpc_v1 fixes observed hidden tiebreaker/stable row order; actual WA/CE/AC sequence gives both1 solved/2161s/shared rank1; post-AC WA ignored, server late-entry clock preserved;18 focused checks plus browser/SQL/callback agreement; [summary/commands/limits](reports/b10-b11-contest-1/README.md); stop before B12 |
| B12 | Restart services and check accepted submissions/results survive | B11 | COMPLETE — PASS; supported full stop/start, same containers/DB volume,4 browser credential sets,11 existing submissions/927 cases and standings unchanged, worker reconnected, new browser submission12 AC103 cases and correct post-AC standings; [summary/commands/limits](reports/b12-restart-1/README.md); interrupted judging recovery NOT TESTED |

Milestone M1: all B01–B12 checks pass on the selected pinned stack. Use stock site pages and operator installation of an already-converted package. This proves the website/judge path; the guided author upload remains C05–C14.

### C. Identity, permissions and author import

Documentation correction (2026-10-30): C18/C19 remain separate rows in this table;
C12 was PARTIAL at that documentation boundary; its subsequent acceptance is
complete in the row below, preserving C05/C07/C10 passes. Deployment order is G13/G04 → G15 → G14 → H03/H05. No runtime tests or
application changes in this correction; validation is recorded in PROJECT_STATUS.md.

Authorized 2026-10-29: C01–C04/C16/C17 are integrated locally; C05 single-ZIP upload is now integrated and accepted locally. C10 private publication and C11 exact-version/hash bridge readiness are now locally
integrated under their 2026-10-30 requests. C12 remaining acceptance is now complete
under its separate request. The later sequential C13/C18/C19 bundle completed probes/password policy, and C18 cutover now complete; do not start Phase D.
Historical checkpoint1 used college ID/password and forced change; this remains
completed evidence, not current target acceptance. C18 and C19 below are implemented and accepted locally. These are
personal-email/no-forced-change adjustments; no public signup or email service.
C15 remains DEFERRED. Preserve existing passwords, data, Phase B evidence and
stock DMOJ templates. No teams/groups/special formats or separate frontend.
Checkpoints: (1) C01/C02/C16/C17/C03/C04; (2) C05–C09;
(3) C10/C11/C12/C13 and integrated browser smoke. C14 is deferred.
C18/C19 remain required before M2/H03; both now pass for scoped local acceptance.
Before schema/data migrations take a private readable backup. Keep raw data in
ignored `build/phase-c-*`; report actual checks in the matching concise
`reports/phase-c-*/README.md` and preserve historical bundles.
Historical canonical ID policy is trim outer whitespace + ASCII uppercase,
rejecting collisions. Retain those IDs unchanged; C18 adds the new canonical-email
key without guessing addresses or merging identities. Checkpoint1 acceptance and limitations: reports/phase-c-checkpoint1-1/README.md. Other rows retain their prior status.


| ID | Task | Depends on | Acceptance evidence |
| --- | --- | --- | --- |
| C01 | Add name/email/student-profile fields only where missing | B01 | COMPLETE — PASS: native owned name/email/Profile round trip and live email isolation; [checkpoint1 evidence](reports/phase-c-checkpoint1-1/README.md) |
| C02 | Historical local login and organizer account recovery | C01 | COMPLETE — PASS: actual offline login/forced change and organizer command recovery in Chromium; [checkpoint1 evidence](reports/phase-c-checkpoint1-1/README.md) |
| C03 | Implement scoped author mode and permission checks | A06,B01 | COMPLETE — PASS for checkpoint1: scoped native admin/routes/lists/files/source/exports and real job authorization; unsafe legacy surfaces disabled; [checkpoint1 evidence](reports/phase-c-checkpoint1-1/README.md) |
| C04 | Test cross-contest, role and participant-email access isolation | C03 | COMPLETE — PASS: native + actual Chromium A/B/role/email/source/event/private-route matrix; [checkpoint1 evidence](reports/phase-c-checkpoint1-1/README.md) |
| C05 | Add private single-ZIP upload with limits | C03,A02 | COMPLETE — PASS for local native/browser acceptance: scoped DMOJ form, CSRF, 32MiB actual-byte cap, private owner record/confirmation/download and fail-closed invalid requests; 8 focused tests and Chromium flow; reviewed total-body bounds/collision cleanup; [summary/results](reports/phase-c-c05-1/README.md) |
| C06 | Harden archive extraction and metadata rejection | C05 | COMPLETE — PASS for extraction-only service integration: 18 archive +6 converter +19 native service/C05/core checks; stored website ZIP reaches strict extractor, supported fixture succeeds, safe errors/attempt cleanup preserve originals; no queue; [C06 evidence](reports/phase-c-c06-1/README.md) |
| C07 | Wrap existing converter as an observable import job | C06 | COMPLETE — local PASS: commit-only scoped queue/status, bounded Celery child, token fencing, safe errors/retry/reconciliation;12 focused checks plus actual supported/failed browser conversions, broker refusal and worker interruption recovery; [C07 summary](reports/phase-c-c07-1/README.md) |
| C08 | Build import findings and compatibility preview | C07 | COMPLETE — local PASS: owner-only escaped stored-output preview, explicit counts/units/standards/scoring, actionable rejection guidance and conversion/judging/publication distinction;28 focused tests + actual Chromium success/refresh/unsupported/role/injection/stale-state checks; stored-output and existing-data/config agreement; [C08 summary/commands/evidence](reports/phase-c-c08-1/README.md) |
| C09 | Add sanitized private statement and asset preview | C08,B06 | COMPLETE — local preview PASS: owner/scoped-author/current-attempt checks, explicit HTML/math allowlists and notices, decoded/re-encoded private PNGs;39 focused tests + actual Chromium raw-response/request-attempt/DOM/access/traversal/spoof/cross-import/retry checks. Real unchanged statement renders30 equations/samples in a supported synthetic conversion; original111MiB archive exceeds unchanged limits, full real-archive acceptance NOT TESTED. Existing data/worker preserved; no judging/publication. [C09 summary/commands/limitations](reports/phase-c-c09-1/README.md) |
| C10 | Publish staged problem versions atomically | C09,B04 | COMPLETE — local private-version PASS: scoped owner/current-attempt/CSRF, durable intent/private fsynced no-replace installation/atomic native rows and audit, immutable receipts, safe session integration;25 focused native +6 installer tests and final Chromium publication, concurrent/failure/process recovery and native/file agreement. Existing data/versions/worker preserved. No contest assignment, public visibility, submission admission or C11/C13 work. Original111MiB archive remains unsupported by unchanged limits; no full-package claim. [C10 summary/commands/limits](reports/phase-c-c10-1/README.md) |
| C11 | Add version/hash readiness check on workers | C10,B03 | COMPLETE — local PASS: authenticated connection-bound fresh worker file/manifest and solution/checker runtime checks at native selection/final send; QU retention/retry, disconnect/reconnect/changed-version/mismatch guards.27 focused tests; one real browser submission16 held without packets/cases across mismatch/reconnect, then dispatched once and AC103/103. Prior data/credentials/versions/sandbox preserved; no C13 probe or new package/language admission. [One summary/commands/limitations](reports/phase-c-c11-1/README.md) |
| C12 | Support import retry and duplicate-package detection | C07,C10 | COMPLETE — local PASS. Reuse passed [C05](reports/phase-c-c05-1/README.md) owner-scoped deduplication, [C07](reports/phase-c-c07-1/README.md) retry/reconciliation/delivery/admission and [C10](reports/phase-c-c10-1/README.md) publication/recovery. Remaining acceptance:3 focused native tests (six overlapping MariaDB connections; mixed-owner races; cross-contest cleanup), six simultaneous authenticated HTTP uploads retain one job/archive, Chromium re-upload returns existing published job24/attempt2/version with audit history intact; another owner receives its own job and mutual access404. Zero new orphan files;1896 prior rows/319 private import files preserved. No application fix or passed-suite rerun required. [One summary/commands/limits](reports/phase-c-c12-1/README.md). Stop before C13/identity migration. |
| C13 | Add a restricted prepublication probe action | C11 | COMPLETE — local PASS; owner/scoped-author/CSRF private known solutions, exact digest/source/runtime binding, quotas/deadline/native resource limits and C11 dispatch.29 focused checks and genuine Chromium→native worker AC3/WA3, callbacks/SQL agreement; prior official results preserved. Internal installed version remains private and participant submission-disabled. [Bundle evidence](reports/phase-c-c13-identity-1/README.md). Later same-version integrated acceptance also PASS: existing imported version2/probe17→official20 WA3/21 AC3/22 AC3→checked standings through explicit private contest admission; immutable manifest/data preserved. [Integrated evidence](reports/phase-c-integrated-1/README.md). |
| C14 | Support multi-ZIP selection with independent job status | C12 | DEFERRED — not implemented; single ZIP suffices; retain multi upload/aggregate/concurrency backlog; [Phase C evidence](reports/phase-c-1/README.md) |
| C15 | Configure and verify optional Google login through native social-auth | C01,C03,C16 | DEFERRED — optional later; verified identity/linking and callback/CSRF checks required before enabling; not completed |
| C16 | Historical canonical college-ID uniqueness and temporary-password gate | C01,C02,A06 | COMPLETE — PASS: canonical DB provisioning/correction races, audited correction, temporary-password gate; legacy credentials/IDs preserved; [checkpoint1 evidence](reports/phase-c-checkpoint1-1/README.md) |
| C17 | Enforce one active session per account | A06,C02,C16 | COMPLETE — PASS: native generation/admission/concurrent-login/logout/reset/poll checks; dispatch after commit, actual AC103 smoke; no device binding; [checkpoint1 evidence](reports/phase-c-checkpoint1-1/README.md) |
| C18 | Migrate provisioned accounts to canonical personal-email login | C01,C16,C04 | COMPLETE — local PASS. Four user-authorized development fixtures assigned addresses with explicit organizer-assigned/unverified-mailbox/non-real-identity provenance; check/apply, complete10-key inventory and guarded email-only cutover. Actual4-account email/password/admin access, ordinary/admin username rejection, no forced change and stale-session checks pass;15 focused native tests include uniqueness races, email-only reset/concurrent sessions and local admin recovery. All password hashes/IDs/history/results preserved. [Closure/commands/recovery](reports/phase-c-c18-cutover-1/README.md). |
| C19 | Remove forced initial/reset password-change gate | C18,C02,C17 | COMPLETE — local PASS for independent password/session policy with C18 cutover now complete. Native provisioned/reset password logs in without forced redirect; optional change retained; outside-app verified admin reset requires reason/attestation, private credential output and audit, with generation/hash revocation. Actual external email/browser first/reset login, stale read/POST/poll, wrong password, voluntary change and role privacy pass; final16 focused bundle checks plus new native participant AC103. Original hashes/accounts/history/standings preserved. [Bundle summary](reports/phase-c-c13-identity-1/README.md). |

### D. Contests and registration

Current scope: supervised, in-person individual competitions. D14 clarifications are
DEFERRED and are not required dependencies. MVP navigation has no standalone
problem archive/problemset, practice, editorials, virtual participation or announcements.

| ID | Task | Depends on | Acceptance evidence |
| --- | --- | --- | --- |
| D01 | Build contest draft form and lifecycle mapping | A07,C03 | COMPLETE — local PASS: scoped native workflow, 8 focused checks and actual Chromium publication/privacy; fresh live worker challenge and preserved data. [D01–D06 summary/commands/limits](reports/phase-d-d01-d06-1/README.md). |
| D02 | Add problem selection, order and labels | D01,C10 | COMPLETE — local PASS: scoped native workflow, 8 focused checks and actual Chromium publication/privacy; fresh live worker challenge and preserved data. [D01–D06 summary/commands/limits](reports/phase-d-d01-d06-1/README.md). |
| D03 | Add schedule/timezone fields and server countdown | D01 | COMPLETE — local PASS: scoped native workflow, 8 focused checks and actual Chromium publication/privacy; fresh live worker challenge and preserved data. [D01–D06 summary/commands/limits](reports/phase-d-d01-d06-1/README.md). |
| D04 | Add one provisioned-account eligibility policy | D01,C04 | COMPLETE — local PASS: scoped native workflow, 8 focused checks and actual Chromium publication/privacy; fresh live worker challenge and preserved data. [D01–D06 summary/commands/limits](reports/phase-d-d01-d06-1/README.md). |
| D05 | Enforce and summarize the one fixed preset, languages and feedback | D02,A07,A10 | COMPLETE — local PASS: scoped native workflow, 8 focused checks and actual Chromium publication/privacy; fresh live worker challenge and preserved data. [D01–D06 summary/commands/limits](reports/phase-d-d01-d06-1/README.md). |
| D06 | Add publication readiness checks | D02,D03,D05,C13 | COMPLETE — local PASS: scoped native workflow, 8 focused checks and actual Chromium publication/privacy; fresh live worker challenge and preserved data. [D01–D06 summary/commands/limits](reports/phase-d-d01-d06-1/README.md). Version4 follow-up PASS: stage-specific errors, real AC103 private probe, exact worker/version readiness and private draft readiness; no reimport or official contest result. [Follow-up](reports/readiness-v4-1/README.md). |
| D07 | Implement pre-start registration/deregistration | D03,D04 | COMPLETE — local PASS: idempotent pre-start registration/withdrawal and concurrent duplicate checks; native leave preserves registration. [Summary/commands/limits](reports/phase-d-d07-d11-1/README.md). |
| D08 | Implement late registration and no late deregistration | D07 | COMPLETE — local PASS: late entry/common end; no withdrawal at/after start, no new registration/submission at end; locked receipt/time/race checks. [Summary/commands/limits](reports/phase-d-d07-d11-1/README.md). |
| D09 | Add basic roster and authorized email visibility | C01,D07 | COMPLETE — local PASS: basic scoped roster with private email; participants/unrelated authors denied; managed CSV deferred. [Summary/commands/limits](reports/phase-d-d07-d11-1/README.md). |
| D10 | Add scoped roster CSV export | D09 | DEFERRED — not completed; retain permissions/formula-escaping requirements if enabled; results export remains F14 |
| D11 | Add scoped participant removal/disqualification with recorded reason | D09,C03 | COMPLETE — local PASS: reason/audit removal retains earned rank; DQ excludes rank, preserves evidence; direct/poll/admission denials, actual browser AC3 and remaining rank1. [Summary/commands/limits](reports/phase-d-d07-d11-1/README.md). |
| D12 | Add scoped editor/reviewer grants | C04,D01 | DEFERRED — additional grant UI not completed; owning author/admin and existing scoped checks remain; no escalation |
| D13 | Add author preview/test submissions | D05,A06 | COMPLETE — local PASS: owner/scoped-admin labelled preview, private archived immutable receipts, native/direct conflict enforcement;6 focused and11 relevant regression checks, actual browser CPP17 AC3/WA3 with complete callback/SQL agreement. Official scores/penalties/ranks/counts/solve statistics unchanged; accounts/passwords/results/sandbox preserved. [One summary, commands and manual steps](reports/phase-d-d13-1/README.md). |
| D14 | Scoped author problem clarifications | — | DEFERRED by user: supervised, in-person competitions; removed from required dependency closure. |
| D15 | Add clone/archive actions | D06 | DEFERRED — not completed; future clone must not copy registrations/submissions |

Retained **Phase D COMPLETE — local PASS**: D01–D09/D11/D13 acceptance passes;
D10/D12/D14/D15 remain deferred. Historical checks are reused, with D13 evidence
above. **Stop before Phase E**; no Phase E work, commit or push authorized.

### E. Participant workspace and feedback

| ID | Task | Depends on | Acceptance evidence |
| --- | --- | --- | --- |
| E01 | Adapt existing DMOJ shell and essential role links | B01 | COMPLETE — scoped author/account links; focused Chromium role navigation passed. Logo pending/nonblocking. [E summary](reports/e01-e02-e04-e05-e17-1/README.md). |
| E02 | Link Problems / My Submissions / Standings | D02,E01 | COMPLETE — common tabs and native paginated own contest list; Chromium participant and denied-user routes passed. [E summary](reports/e01-e02-e04-e05-e17-1/README.md). |
| E03 | Custom statement/editor split | — | DEFERRED — reuse separate native problem/submit pages; narrow-view usability remains E14. |
| E04 | Reuse native Ace and validated language selector | E02,B03 | COMPLETE — native Ace/editor/file load and actual browser submission26 AC3/3 passed on new temporary live contest. [E summary](reports/e01-e02-e04-e05-e17-1/README.md). |
| E05 | Isolate existing native saved-code keys | E04 | COMPLETE — v2 account/contest/problem/language key; same-browser cross-account, contest and two installed problem/language checks passed; legacy recovery explicit. [E summary](reports/e01-e02-e04-e05-e17-1/README.md). |
| E06 | New draft sync/autosave and offline infrastructure | — | DEFERRED — keep useful existing features; E05 fixes retained native saved-code isolation only. |
| E07 | Dedicated custom-input Run contract | — | DEFERRED — A12 historical design retained; no new runner required. |
| E08 | Custom-input Run infrastructure/panel | — | DEFERRED — C13 probes and D13 author tests retained; no participant custom Run requirement. |
| E09 | Reuse native submit with durable contest receipts | E04,B08,D08 | COMPLETE — live same-key first-response-discard/retry returned submission30 twice, one receipt, actual AC3/3. Earlier attempt iterations27–29 are separate real submissions. [Evidence](reports/e09-e15-1/README.md). |
| E10 | Link native paginated own submissions | E09 | COMPLETE — live account/contest list and direct denial; isolated 52-row/2-page/filter/empty test passes. [Evidence](reports/e09-e15-1/README.md). |
| E11 | Reuse native status/case details | E10,B09 | COMPLETE — displayed stored case numbers; actual submission30 cases1–3 AC, isolated skipped case7 explicitly says not run. Existing WA/CE/RTE/TLE evidence retained. [Evidence](reports/e09-e15-1/README.md). |
| E12 | Verify retained feedback/privacy guards | E11,D05 | COMPLETE — direct source/case pages and poll scoped in browser; four focused tests cover hidden checker output and revoked scope/session. [Evidence](reports/e09-e15-1/README.md). |
| E13 | Reuse authenticated polling/refresh | E10 | COMPLETE — interrupted general poll, refresh and re-login reached stored AC; replaced session and removed entrant denied. [Evidence](reports/e09-e15-1/README.md). |
| E14 | Check basic browser usability | E01,E11 | COMPLETE for checked pages — keyboard filter/focus, 375/640px widths and CSS 200% zoom; fixed native tab placement and select overflow. [Evidence](reports/e09-e15-1/README.md). |
| E15 | Verify native fallback/error/empty states | E04,E13 | COMPLETE for checked states — Ace asset failure plain textarea made real submission31 AC3/3; draft, blank-source validation, empty filter and isolated queued/no-worker pages passed without false verdict. [Evidence](reports/e09-e15-1/README.md). |
| E16 | Additional language | — | DEFERRED — preserve every existing enabled/approved language and its evidence; no extra-language work. |
| E17 | Finish eligible homepage and authorized navigation | E01,D04,D08,C18,C19,C17 | COMPLETE — eligible/empty home, upcoming/active/ended actions, role/removed denial and anonymous email-login redirect passed in Chromium. [E summary](reports/e01-e02-e04-e05-e17-1/README.md). Author-menu follow-up preserved scoped actions and selected the original published problem in a private draft. [Follow-up](reports/author-navigation-1/README.md). Current branding/navigation follow-up PASS: plain-text brand, no role-mode label, Calendar or footer UI-language selector; compiler selection and participant restrictions retained. [Follow-up](reports/navigation-branding-1/README.md). |

Milestone M2/local acceptance requires retained A–D gates and E01/E02/E04/E05/E09–E15/E17.
F08/F10/F11/F14 are a bounded operations follow-up: inspect/reuse native tools
and add only missing access, history, correctness or export/final-state checks.
No new requirement passes from source inspection or stitched historical runs.

### F. Deferred teams/matches and individual contest operations

| ID | Task | Depends on | Acceptance evidence |
| --- | --- | --- | --- |
| F01 | Map individual/team entry identity onto site models | A07,B10 | DEFERRED — shared/team identity; native individual participation stays in MVP; not completed |
| F02 | Add team creation, invitation and acceptance | F01,D04 | DEFERRED — teams; not completed |
| F03 | Add membership uniqueness and roster locking | F02,D08 | DEFERRED — team rosters; not completed |
| F04 | Implement exactly-two-entry match presets | F03 | DEFERRED — special 1v1/2v2/XvX modes and selectors; not completed |
| F05 | Add team-aware submission attribution | F03,E09 | DEFERRED — shared attribution; not completed |
| F06 | Implement or adapt team score aggregation | F05,B11 | DEFERRED — team scoring; not completed |
| F07 | Build team standings and permitted team submission views | F06,E12 | DEFERRED — team standings; not completed |
| F08 | Verify retained fixed scoring cases | B11,D08 | NATIVE REUSE — ties/late-entry evidence exists in B11/D07; verify combined journey and any changed scoring path only. Pending closure. |
| F09 | Add multi-test group/dependency scoring fixtures | A03,B09 | DEFERRED — extended partial-scoring coverage; not participant groups; existing converter/judge group fixtures and evidence preserved |
| F10 | Reuse bounded native operator rejudge | C10,B09 | SMALL ADAPTATION — native tools/reversion exist but current route policy blocks actions; verify scoped access, old cases/history, exact version and audit before enabling. Pending; no broad admin grant. |
| F11 | Verify authoritative replacement and stale results | F10 | SMALL ADAPTATION if required — native packets identify submission, not a new attempt token. Prove safe serialized rejudge/fencing and pending credit handling; no invented protocol fields. Pending. |
| F12 | Add standings freeze and reveal | E12,F08 | DEFERRED — optional operation; MVP live standings, no freeze selector; not completed |
| F13 | Add logged live extension and controlled problem correction | D06,F10 | DEFERRED — not completed; retain deadline/version/audit/rejudge requirements for future enablement |
| F14 | Reuse finalization/results export where sufficient | F11,F08 | NATIVE REUSE / gap assessment — roster export is not results export; no managed finalization action found in inspected URLs. Verify native coverage, add only missing scoped final/pending/error gate and matching export. Pending. |
| F15 | Add separate practice/virtual participation | F14 | DEFERRED — not completed; future attempts must never alter official results |

### G. Single-server operational readiness; optional expansion

| ID | Task | Depends on | Acceptance evidence |
| --- | --- | --- | --- |
| G01 | Separate coordinator and worker deployment settings | B12 | No worker requires the full application database |
| G02 | Pin/build/document the deployable worker image | A03,G01 | Image identity and executors recorded |
| G03 | Add worker enrollment/revocation and network configuration | G02 | Unauthorized/revoked worker cannot join |
| G04 | Synchronize private problem versions with hash checks | C11,G03 | Corrupt/stale package rejected before execution |
| G05 | Join a second trusted laptop worker | G04 | DEFERRED — not completed; initial isolated worker on college server suffices |
| G06 | Test worker loss during compile and execution | G04 | Safe retry on the initial worker; no false contestant verdict; second worker not required |
| G07 | Test reconnects and duplicate/late completion delivery | G06,F11 | Single authoritative score update |
| G08 | Add basic protected queue/worker health view | G04 | Authorized operator distinguishes queued/offline/stale/incompatible initial worker; elaborate dashboards DEFERRED |
| G09 | Build heterogeneous-machine calibration and pool policy | G05,A11 | DEFERRED — not completed; required before advertising heterogeneous pools |
| G10 | Measure representative target-server load | G08,G02 | COLLEGE-SERVER CHECKLIST — separate from local acceptance; choose actual event workload and record measured capacity. No fixed 150+/300 guarantee. |
| G11 | Add separate 300-request burst guarantee | G10 | DEFERRED — not completed; G10 measures chosen MVP burst; no untested 300-request claim |
| G12 | Custom Run contention testing | — | DEFERRED with E08; no local-demo dependency. |
| G13 | Exercise backup and restore to a fresh isolated deployment | B12,C10 | Accounts, rules, source, results and private problem versions recovered without touching the existing deployment |
| G14 | Verify approved campus reachability | G15,G03,C19 | COLLEGE-SERVER CHECKLIST — login/submit/results over approved reachable campus network; internet independence optional. No host-network changes here. |
| G15 | Stage/rehearse laptop-to-college-server deployment before LAN acceptance | G13,G04 | After G13 fresh isolated backup/restore acceptance and G04 version/hash readiness, deploy website/DB/Redis/background services and isolated worker on the college server; verify local service health and preserve settings separation/auth/private versions. Actual campus/guest access is tested next in G14; not a prerequisite for staging. |
| G16 | Write concise start/stop, backup/restore, incident and worker-recovery guide | G07,G13,F14 | Another operator can recover initial worker and finalize safely; no elaborate dashboard required |

### H. Release and later desktop work

| ID | Task | Depends on | Acceptance evidence |
| --- | --- | --- | --- |
| H01 | Audit scope checks, uploaded content, identity/session and private-data routes | C04,C18,C19,C17,E12,D11 | Named negative cases pass; no participant-email leak or removed-entrant access; deferred freeze not required |
| H02 | Review version pins, support status, notices, secrets and deployment defaults | G02,H01,A09 | Supported deployed framework verified; no private package/secrets in tracked source |
| H03 | Run minimum local browser journey | B12,C12,C18,C19,D06,D08,D09,D11,D13,E02,E05,E09,E12,E14,E15,E17 | PENDING — one newly executed author import/preview/probe/create/publish → participant email login/register/problem/native submit/actual verdict/standings; author unranked and unauthorized/removed denial. No deployment/load prerequisites. |
| H04 | Fix concrete journey blockers | H03 | PENDING — rerun affected checks only; preserve existing history, pins and isolation. |
| H05 | Publish local tested envelope and separate server checklist | H04 | PENDING — tested local URLs/manual steps/limitations; operations checklist includes production, campus network, restore, worker recovery and representative load. No public-deployment claim. |
| H06 | Write a separate desktop/OS feasibility matrix | H05 | DEFERRED — not completed; future per-OS controls, permissions and limitations |
| H07 | Define web-to-desktop session/configuration contract | H06 | DEFERRED — not completed; server remains authoritative; browser identity is no security claim |
| H08 | Implement one native-platform proof of concept | H07 | DEFERRED — not completed; future enforced control and failure/recovery demonstration |

Tasks H06–H08 do not block a normal website release. An ordinary webview wrapper is not a secure exam browser.

## 15. Parallel Codex workflow

Use independent Git worktrees/branches for independent code tasks. Official OpenAI documentation describes worktrees as separate checkouts for parallel chats.[5] The supplied Agentastic article illustrates the same workflow; an additional orchestration product is optional.[6]

Current user instruction: use one agent. The optional parallel workflow below is retained for later separately authorized work. Start with one guided agent until you can explain the website/submission path and inspect its changes. After M1 and stable contracts, try two independent implementation workstreams with one integration/review owner. On the 16 GB development laptop, avoid running several full site/database/judge stacks and heavy builds simultaneously.

Suggested ownership once M1 and contracts are stable:

| Workstream | Owns | May run alongside |
| --- | --- | --- |
| Site/permissions | Scoped access, author pages, lifecycle integration | Editor and isolated import work with frozen contracts |
| Import/judge integration | Package jobs, version installation and compatibility | UI against documented fixtures/contracts |
| Participant UI | Native templates, essential links and display states | Backend work through stable API fixtures |
| Operations/testing | Worker deployment, load definitions, recovery | Feature work after interface baselines |
| Integrator/reviewer | Shared schema, migration ordering, final contract decisions and merges | Reviews completed branches |

The same developer/agent may hold these roles sequentially. A table of roles is not a requirement to run five agents at once.

Rules for parallel work:

1. One task, branch and worktree per implementer.
2. Each task names allowed paths, interfaces, dependencies and acceptance checks.
3. Start tasks from a known integrated commit; dependent tasks wait for that contract/implementation.
4. Give database schema/migrations one owner at a time.
5. Shared dependency locks, routing and central configuration also require explicit ownership.
6. Use separate ports, test databases, Redis namespaces and output directories for concurrent environments.
7. Never test parallel migrations against the same production or shared test database.
8. Review each diff, run its checks, merge sequentially and run the integration checks on the combined result.
9. A reviewer checks evidence and behavior; agreement between agents is not proof.
10. Agents must label mocked, inspected and actually executed paths differently.
11. Do not let agents commit private test ZIPs, credentials or student records.
12. Record blockers without replacing an actual judge integration with fake successful verdicts.

Reusable task prompt:

> Work on task <ID> only in the assigned branch/worktree. Read AGENTS.md, PROJECT_STATUS.md, the actual implementation plan, the current compatibility report and relevant existing contracts. Verify dependencies are present. Allowed paths: <paths>. Preserve existing converter behavior, pins and fixtures unless this task explicitly changes them. Reuse DMOJ functionality before adding custom code. Implement the smallest complete change and its meaningful acceptance checks. Do not modify unrelated modules, shared schema or dependency locks without coordinating with the owner. Report files changed, commands and exit statuses, actual observed results and remaining limitations. Do not claim judging success from conversion or mocks.

First Codex assignment:

> A01 orientation is complete. Read PROJECT_STATUS.md and section 19, perform only the user-requested task, record measured evidence and update progress. Keep terminal output brief; do not start the next backlog task automatically.

## 16. REA and other tools

REA describes itself as reverse-engineering tooling for application behavior and binaries.[7] It may help answer a focused future question about an authorized application, with evidence and limitations.

It is not a judging backend, contest platform, permission system or secure-browser foundation. For this website, source inspection of DMOJ and normal browser/UI tests provide more direct value. Keep REA optional and outside the runtime dependencies.

Use the existing DMOJ visual shell: horizontal navigation, centered content,
compact tables, sidebar styling and footer. Adapt its templates for eligible
contests, essential navigation and the three contest tabs in section 9; no
separate frontend. Keep the plain-text Contests-CPJudge header. A visual reference does not determine
scoring semantics; section 5 is the single authoritative MVP preset.

Add tools only for a concrete missing capability. Reasonable candidates after repository inspection include browser automation for journeys, load testing for bursts, and local math rendering. Pin chosen versions and serve required runtime assets locally.

## 17. Later native SecureExam client

The website release should already have stable URLs, a small documented client API, server-side rules, locally served assets and a feature/configuration boundary. These support reuse in a later native client.

A desktop client can load the same contest UI. The server, hidden tests and judging infrastructure remain server-side.

The OS-specific security layer is separate: Windows integration, macOS assessment support and a defined Linux examination environment require their own current feasibility and permission checks. Do not finalize desktop frameworks just to match the frontend language.

Reserve future concepts such as exam-session policy, client minimum version, session heartbeat and proctor recovery, but do not build unused native stubs throughout the website.

The later server must not treat a user-agent string, JavaScript flag or self-reported heartbeat as proof of lockdown. Any stronger trust claim needs an explicit threat model and validated enforcement. Reuse of the website saves UI work; it does not automatically deliver secure examination controls.

## 18. Local acceptance and separate college-server readiness

The minimum local website is complete only after the current H03 journey runs
through native pages: author email login → one supported ZIP import/safe preview/
actual bound probe → ordered/scheduled contest publication → participant email
login/registration → native problem/editor/submit → actual verdict/cases → correct
fixed standings. Also test private unranked author submissions, unauthorized and
removed-user direct/poll denial, and retained session/source/CSRF protections.
Historical A–D evidence remains complete within its original boundary; it does
not complete this new combined journey. F08/F10/F11/F14 retain bounded operations
checks before claiming safe rejudge/finalization/export.

Use existing native pages and small targeted adaptations. Missing logo artwork,
Monaco, split layout, draft sync/new autosave, custom Run, extra languages,
cosmetic redesign, teams/groups/special matches/ratings/practice/virtual,
announcements/clarifications/multi-ZIP and secure browser work are deferred.
Preserve useful existing features and upstream backend internals.

One server with isolated worker suffices. Production configuration, approved
reachable campus network, fresh backup/restore, worker recovery and representative
load are separate college-server checks, not prerequisites to finish a local demo.
Internet is allowed; offline independence is optional. No fixed user/request
capacity, distributed pool, second laptop or public exposure is required. No
untested operational claim. The original 111 MiB package has its own completed
local import-to-judging proof under the bounded limits above; E09–E15 focused
acceptance remains recorded above. The broader H03 journey remains a separate
pending gate.

## 19. Task workflow and persistent status

The user learns through a separate ChatGPT conversation. Do not create learning
documents, exercises or long Q&A in the repository or terminal. Keep the user-authorized task or task bundle as the active unit; do not cross
its boundary automatically. For a bundle update status after each task.

1. Read AGENTS.md, PROJECT_STATUS.md and this actual implementation plan. This plan
   currently lives at the repository root; do not move it or create the proposed
   directory tree merely to match an example path.
2. Inspect Git status, relevant source and existing evidence; preserve user work,
   attribution, dependency pins, private inputs and previous runs.
3. Complete the requested task and its applicable checks. Investigate failures
   before narrow fixes. Use new output directories, and separate conversion checks,
   actual judging, historical inspection, mocks and untested behavior.
4. Store private raw logs/data under ignored build/ and sanitized commands, exit
   statuses, versions and result summaries under reports/. Never report tests as
   passed unless they actually ran.
5. Update PROJECT_STATUS.md and the task's acceptance/status row after completion:
   goal/current architecture, completed tasks/evidence, current and next task,
   working commands/latest results, decisions, blockers and untested features.
   Consolidate useful unique facts and user-written notes before removing old docs.
6. Finish with a brief PASS/FAIL/BLOCKED status and evidence paths. Stop at the
   requested task boundary; commit/push only when explicitly authorized.

### Contribution and release evidence

Open-source integration can be substantive engineering. The evidence should show the parts you designed and verified.

| Reused foundation | Potential SecureExam contribution | Evidence to retain when implemented |
| --- | --- | --- |
| DMOJ execution sandbox/runtime | Safe integration and compatible deployment | Recorded source/image pins; real verdict probes |
| Existing converter/writer | Strict import validation and website publication | Supported/rejected packages, regression results and error examples |
| DMOJ contest system | Individual registration, scoped roles, fixed preset and entrant removal | Rules document, focused code diffs and race/access checks; team work deferred |
| Native Ace and DMOJ templates | Essential scoped navigation and safe saved-code isolation | Minimal patches and actual browser journeys |
| Existing worker support | Reproducible authenticated enrollment, exact-version routing and recovery | Initial isolated worker on single server, disconnect/reconnect test and measured workload; extra machines deferred |

Maintain these documents gradually in the real repository:

- docs/architecture.md: current architecture and data flow, including what actually runs.
- docs/decisions/: short decisions with alternatives and reasons.
- PROJECT_STATUS.md: current goal/architecture, completed and current/next tasks, evidence, commands/results, decisions and blockers.
- reports/: measured compatibility, reliability and load results.
- README.md: setup, a working demo path, supported scope and limitations.
- A brief upstream/contribution map: reused source, local modifications and original modules.

Use small commits tied to completed behavior. Keep one or two debugging accounts with the symptom, hypothesis, evidence, fix and regression check. You should be able to rerun setup and explain a submission from browser to verdict.

Do not claim to have written the DMOJ judge/sandbox, supported 300 submissions, deployed a multi-worker system or built native lockdown unless the relevant work and measurements actually exist.

## Sources checked

These establish upstream capabilities and tooling behavior. Product rules and task estimates in this plan are recommendations; they are not claims of already implemented upstream behavior.

1. DMOJ website source and features: https://github.com/DMOJ/online-judge
2. DMOJ judge server: https://github.com/DMOJ/judge-server
3. DMOJ site installation: https://github.com/DMOJ/docs/blob/master/docs/site/installation.md
4. Monaco editor: https://github.com/microsoft/monaco-editor
5. Official OpenAI worktree guidance: https://learn.chatgpt.com/docs/environments/git-worktrees
6. User-supplied parallel-workflow article: https://www.agentastic.dev/blog/run-codex-agents-in-parallel
7. User-supplied REA repository: https://github.com/morluto/rea
8. DMOJ website requirements inspected: https://github.com/DMOJ/online-judge/blob/master/requirements.txt
9. Django 4.2 support ended: https://www.djangoproject.com/weblog/2026/apr/07/security-releases/
10. Django 4.2 Python support: https://docs.djangoproject.com/en/4.2/releases/4.2/
11. DMOJ contest/participation source inspected: https://github.com/DMOJ/online-judge/blob/master/judge/models/contest.py
12. Official OpenAI guidance on task scope, AGENTS.md and verification: https://learn.chatgpt.com/docs/learn/best-practices

