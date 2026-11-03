# CPJudge minimum website dependencies

Updated 2 November 2026. Current authorization is **inspection/documentation only**,
following the user's final “no implementation for now”. Application changes and
new live acceptance are pending. [Plan](SecureExam-Implementation-Plan.md),
[status](PROJECT_STATUS.md), [one review summary](reports/minimum-native-review-1/README.md).
Completed evidence and all runtime/source pins stay intact. This selection
supersedes the earlier larger MVP dependency closure, without changing historical
acceptance or removing useful implemented features.

## Product and preservation

Organizer-provisioned personal email/password, canonical email uniqueness, no
signup/Google/email delivery/forced change; retain audited organizer recovery and
one active session. Eligible contests at home, essential authorized role links;
Problems, My Submissions, Standings in each contest. Authors upload one Polygon
ZIP, preview/probe it, select/order immutable problems, schedule/publish, manage
entrants and test privately without ranking. Participants register under existing
rules, read problems, enter/load source in native controls, submit and see actual
verdicts/cases/standings. Keep the fixed individual ICPC/20-minute preset.

Reuse native DMOJ templates, Ace, problem/submission/case pages, pagination,
standings, authenticated polling and worker transport. Retain custom code already
needed for strict imports, immutable versions, scoped permissions, atomic receipts,
identity/sessions, fixed scoring and private author tests. New custom code needs a
concrete gap. Do not remove upstream backend features when hiding navigation.
Preserve accounts/password hashes/imports/source/results/audits, archive/CSRF/
private-file protections, exact-version checks and judge isolation.

**Original 111 MiB ZIP remains unsupported** by unchanged 32 MiB upload / 128 MiB
conversion limits. Smaller fixtures do not prove full-package support. No limit,
language standard, checker, scoring or sandbox change is part of simplification.
Approved Foobar artwork is missing but nonblocking; retain current mark/attribution.

## Classified work and dependency order

Categories describe implementation decisions, not new test passes. Exact source
paths and historical acceptance links are in the review summary.

| Tasks | Classification | Remaining acceptance |
| --- | --- | --- |
| A01–A12, B01–B12 | Already satisfied within historical scope | Reuse foundations/actual verdict/standings/completed-result restart evidence; A12 is design only, no Run implementation claim. |
| C01–C13/C16–C19 | Already satisfied, retained local gates | Email-only active; strict single-ZIP/private preview/publication/probe/readiness/retry/session evidence retained. No new import test this review. |
| D01–D09/D11/D13 | Already satisfied, retained local gates | Contest schedule/order/publication, registration/removal/DQ and persisted private author tests passed. D13 is complete; old stop-before-D13 text is obsolete. |
| E01/E02/E17 | Necessary small adaptation | Root already redirects to filtered native contests; finish role links and consistent three contest tabs, truthful actions/counts and empty states. No redesign. |
| E04/E09–E13/E15 | Native reuse; small fixes only for demonstrated gaps | Reuse Ace, language/source/native admission, own paginated submissions, cases and polling. Verify file loading and fallback; inspected form has no file chooser. Retain durable retry key. |
| E05 | Necessary small privacy adaptation | Existing Ctrl-S/restore key is language-only; isolate retained saved code by account/contest/problem/language. No new draft service. |
| E12/E14, H01 local cases | Native reuse / targeted checks | Check direct/source/case/poll/privacy, removal/session denial, CSRF, keyboard/zoom/narrow/failure states; change only reproduced blockers. |
| F08 | Native reuse | Reuse fixed scorer and tie/late-entry evidence; check final combined journey and any changed path. |
| F10/F11 | Native reuse plus necessary access/correctness assessment | Native rejudge/reversion exists; policy currently blocks routes. Verify bounded scoped action, retained old cases/audit, pending-credit and stale-result safety before enabling. No broad admin grant or invented protocol. |
| F14 | Native reuse where sufficient; small adaptation for confirmed gap | Current managed URLs have no finalization action; roster export does not satisfy results export. Check native coverage before adding pending/error/final-state guard and matching scoped export. |
| H03/H04/H05 | Necessary new local acceptance, still pending | Run one combined real browser journey, fix concrete blockers, rerun affected checks, report tested envelope. Historical runs alone cannot pass this gate. |
| G01–G04/G06–G08/G10/G13–G16, H02 production portions | Separate college-server checklist | Preserve existing local evidence; production/network/restore/recovery/load acceptance is not completed and does not block local demo. |

Implement later in this order, with one agent:

1. E01 → E02/E17, reusing C18/C19/C17 identity and D04/D08 eligibility rules.
2. E04 → E05/E09 → E10/E11 → E12/E13/E15; E14 checks actual pages. Verify the
   complete native widget path first; if file selection is absent, add only a
   bounded loader into the existing source field and native submit endpoint.
3. H03 depends on B12/C12/C18/C19/D06/D08/D09/D11/D13 and
   E02/E05/E09/E12/E14/E15/E17. Execute author import/preview/actual probe →
   create/select/order/schedule/publish → participant email login/register/problem/
   native submit/actual verdict/correct standings, with unranked author and
   unauthorized/removed-user checks. Preserve expired fixtures; use a fresh
   supported bounded package/contest if actual time has elapsed.
4. F08/F10/F11/F14: bounded operations follow-up; inspect native tools, reuse
   revision support, expose only safe scoped actions and verify replacement/history/
   finalization/export. These are not an excuse to rebuild judging.
5. H04 fixes affected local blockers; H05 records actual local results/limitations
   and separates the server checklist. No new runtime completion is claimed here.

A private readable backup is required before any later migration; avoid schema
changes when existing native structures suffice. Do not reset data or credentials,
repeat passed broad suites, add evidence frameworks, commit, push or expose publicly.

## Deferred work

E03 split/resizing; Monaco portion of E04; new autosave/sync/offline infrastructure
E06; custom Run E07/E08 and its G12 contention test; extra language E16; cosmetic
redesign. Existing native saved-code behavior is preserved with E05 isolation.
C14 multi-ZIP, C15 Google, D10/D12/D14/D15 extra management/clarifications,
F01–F07 teams/special matches, F09/F12/F13/F15 extended scoring/freeze/live
correction/practice/virtual, groups/ratings/matchmaking/announcements and H06–H08
secure browser remain deferred. Preserve completed features and historical evidence.
G05/G09/G11 second worker/heterogeneous pool/300-request guarantee remain deferred.
Internet independence is optional, not a release prerequisite.

## College-server checklist — separate from local journey

One server hosts website, DB, Redis/background services and isolated worker.
Participants need reachable server networking and account login. Do not change
host-wide networking or perform these tasks for the local demo.

- Production configuration: supported tested pins, secrets/allowed hosts/HTTPS,
  static/private routing, internal service exposure, time sync and operator health.
- Approved reachable campus network: verify actual participant routes to the
  server; internet is allowed, public-internet independence optional. No public
  deployment/VPN/network-policy change without separate authorization.
- Backup/restore: fresh private backup, restore to an isolated target and verify
  accounts/hashes/import versions/source/results/audits before staging (G13 → G15).
- Worker recovery: interrupt compile/execution, reconnect, verify retry and stale/
  duplicate-result safety and document incidents (G06 → G07 → G16). B12 graceful
  idle restart does not prove this.
- Representative load: choose actual event workload on target hardware, measure
  website latency, failures, bounded judging, queue/drain time and resources.
  No fixed 150+ user, 300-request, second-laptop or distributed-pool prerequisite.

No server details are needed for this documentation review. Those later tasks
need college hardware/access, approved campus routes, operator configuration and
an expected event workload. Local implementation/live journey remains pending
because of the explicit documentation-only boundary, not an external blocker.
