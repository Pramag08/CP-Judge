# CPJudge project status

Updated 2026-11-08. Plan: [SecureExam-Implementation-Plan.md](SecureExam-Implementation-Plan.md)
(actual root location). Read this file and [AGENTS.md](AGENTS.md) before work.
Current MVP task selection: [MVP_DEPENDENCIES.md](MVP_DEPENDENCIES.md).

**Organizer ZIP default 1200:1 (2026-11-08): PASS, local.** The existing `CPJ_ARCHIVE_LIMITS` now sets 1200 for all organizer uploads; #69's exception entry was removed. Central-directory preflight and streamed extraction use the same effective ratio, while 128 MiB upload/member, 320 MiB total, 1024 entries, path/type and worker resource limits remain. Original #69 passed strict extraction under the default without an override (300 entries, 106,749,143 actual bytes); its published version7 and real D/AC101 result were unchanged. Twenty-one focused archive tests, one Django setting test and live status passed. The inspected #69 Polygon configuration is faithfully handled; arbitrary noninteractive packages with other scoring/checker/testset semantics remain explicitly unsupported, so universal compatibility is unproven. [Commands and limits](reports/foobar-zip-default-1200-1/README.md). No commit/push; next work only on a concrete requested compatibility feature.

**Historical Test1 ZIP #69 continuation (2026-11-08): READY TO ADD, local real judge PASS at that boundary.** Isolated strict extraction of the original SHA-matched ZIP under the then-job-only 1200:1 ratio counted 106,749,143 actual streamed bytes; all 12 high-ratio entries were among 101 tests' required inputs/answers. The default was then 100:1, and an isolated resource-bounded conversion retained 101 test hashes, five samples, ungrouped one-point scoring, 2s/524288KiB, CPP17 checker. Job69 had already reached successful queued attempt3 when resumed. Authenticated publication retry produced immutable version7; after exact 16-file worker installation, its CPP23 reference probe was real D/AC on 101/101 stored AC cases, and the author page showed Ready to add. The version was not added to Test1. [Historical commands](reports/foobar-zip-limit-2/README.md). No commit/push.

**Historical Test1 ZIP #69 ratio diagnosis (2026-11-07): COMPLETE — local metadata check at that boundary.** The original ZIP was then private and unextracted. Central-directory inspection found the first rejection at test-data entry41: 485,719/1,455 bytes = 333.83:1 versus active 100:1 per-entry cap. Twelve test-data entries exceeded it; max 986.85:1. Total expanded 106,749,143/335,544,320 bytes, largest 2,002,015/134,217,728, entry count 300/1,024 and overall ratio 2.44:1 were within their applicable caps. Job69 was then failed; its stored/browser error named the exact check, measurements and limit. A 1200:1 cap passed a central-directory-only candidate check but was not then applied pending confirmation the files were required. Eighteen archive and one isolated site test plus authorized Chromium error display passed; no conversion or judging of #69 at that boundary. [Historical measurements](reports/foobar-zip-limit-1/README.md). No commit/push.

**foobar ZIP import and Test1 upload #64 (2026-11-07): local PASS.** The failed XML trigger was test 1's inert `description="Added Sample testcases"`, not per-test points; Test1 uses fixed ICPC/20-minute scoring. The strict converter accepts this annotation and still rejects per-test points. The upload/status pages now show one heading, draft name/limit, automatic conversion and refreshable judge progress with safe package/temporary actions. Upload #64 final attempt 3 succeeded; immutable version 6 was installed exactly on the existing worker, real reference probe AC on 15 cases, and Chromium added B/order 1 to Test1. Separate modified job68 failed with a specific per-test-points correction. Seven converter and three isolated HTTP tests passed; existing draft A/scoring, access and limits were retained. [Evidence, exact commands and browser retest](reports/foobar-zip-import-1/README.md). No commit/push; next task only on request.

**foobar organizer simplification (2026-11-04): local PASS.** One agent kept the supplied logo, header order, account menu and Results gate; simplified sign-in/footer and grouped the native draft, problem, participants and publish pages. A bounded Celery reference check judged a new exact version AC on 103 cases; missing check blocked publication. Disposable private `simplify26` was created, uploaded, scheduled, published and entered in Chromium; separate participant submission39 was AC/103. Hide/Unhide, Remove, DQ, direct-route denial, Running · Private badge, exact footer and Results passed. Additive migrations0013/0014 followed an ignored private DB backup; 23 focused tests and live ORM assertions pass. Existing data was not reset or rejudged. [Click path, commands, evidence and limits](reports/foobar-organizer-1/README.md). No commit/push; next task only on request.

**foobar header and read-only Results (2026-11-03): PASS.** Supplied logo is in the existing header and favicon; site/page/admin titles use `foobar`. Contests precedes authorized-only Author Contests, with keyboard-operable account chevrons and no role switcher or broken contest Admin tab. Past rows link to permitted standings; ended join POSTs return 403 before virtual creation. Staff/participant Chromium checks, private ranking denial, participation count 2→2 and 14 focused entry tests pass. Existing virtual records and official standings were preserved. [Commands, evidence and limits](reports/ui-foobar-virtual-1/README.md). H03 remains pending; no commit or push.

**Navigation and branding simplification (2026-11-03): PASS.** `b01-staff` retains active admin/superuser and explicit author capabilities without a role-mode selector; Chromium opened participant contest pages, Create contest and scoped import management in one session. Shared DMOJ templates now show plain-text **Contests-CPJudge** in the header and site/admin titles; Calendar and footer UI-language selector are absent, while native CPP23 submission language selection and upstream footer attribution remain. Participant author links/routes stay denied. No backend policy, data or sandbox change; 32 imports, 4 versions, 14 contests, 37 submissions and 2 private unranked author tests remain. [Checks, paths and limits](reports/navigation-branding-1/README.md). H03 remains pending; next work only on request. Browser login may replace an older account session.

**Version4 readiness diagnosis and repair (2026-11-03): PASS.** Published `pv900000000000000004` was valid, but lacked an owner AC probe, contest approval, enabled language and exact worker advertisement; `navproof26` also had an expired draft start. Existing immutable installer, real CPP23 probe4/submission37 AC103/103, author schedule form and re-selection resolved each gate. Live `readiness(navproof26) == []`; draft remains unpublished. Readiness errors now identify the failing stage, with one focused D06 test passing. The older `b03-status` anonymous-401 health-check bug was already repaired; current full status exits0. [Exact checks, failures, preservation and limits](reports/readiness-v4-1/README.md). No reimport, existing-result change, sandbox change, commit or push. H03 remains pending; next work only on request. The owner browser proof may invalidate an earlier `b01-staff` session.

**Author navigation follow-up (2026-11-03): PASS.** `b01-staff` already had explicit author identity and an active `problems.publish` grant on `icap111a`; the original Polygon import remains owner `C1LIVEA`, job58, private published version3 (`pv900000000000000003`). The role menu now has a visible Author trigger to existing Create contest and Manage contests / imports routes. Chromium created unpublished `navproof26` and selected that existing version; scoped import opened, while participant menu/direct author routes were denied. No reimport or judging. [Exact URLs, checks, decisions and limits](reports/author-navigation-1/README.md). H03 remains pending; next work only on request. The browser proof logged into `b01-staff`, so an earlier browser session may need sign-in again under the one-active-session policy.

**Latest local startup review (2026-11-02): PASS.** B02 start now waits up to
20 seconds for bridge/Celery; B02 status fails on missing processes or an event
state inconsistent with polling mode. Top-level status requires DB/Redis/worker
containers and native worker online/executors; start gates its success on that
status. A fresh Chromium email login and labelled submission36 AC/103 cases passed.
Supported idle stop/start, status, post-restart Chromium login, saved verdict,
worker reconnect/exact-version advertisement and private readiness socket passed.
Named DB volume and worker isolation settings were preserved. [Checks and limits](reports/startup-review-1/README.md).
Next task remains the previously selected MVP work only on request.

**Latest local lifecycle repair (2026-11-02): PASS.** The apparent `b03-status`
failure was an anonymous `/status/` HTTP 401 under the active scoped policy;
worker container/native state checks had passed. `b03.py` now checks native worker
state, website login 200 and the expected anonymous 401. `manage.py start` and
`status` exit 0; Chromium email login and labelled submission35 AC on 103/103
stored cases pass, with the connected CPP23 worker advertising its exact version.
No reset/data/configuration change. [Commands, evidence and limits](reports/startup-status-fix-1/README.md).
Next task remains the previously selected MVP work only on request.

## Goal and current architecture

Build **CPJudge**, a minimal individual-contest website around DMOJ judging and
strict Polygon imports; SecureExam desktop lockdown is later work. Target: eligible
contest list at home, supplied foobar logo top left and scoped account/author
actions top right, without a role-mode switch. Contest navigation is Problems, My
Submissions and Standings. One ordinary contest path serves any **tested supported
participant count**, with separate submissions/scores/ranks and the single fixed
Individual ICPC/20-minute preset in plan section 5. No participant-format selector.

Authors create/edit contests, import ZIPs, manage/remove entrants. Problem clarifications (D14) are deferred for
supervised, in-person competitions. Target identity is administrator-provisioned personal email/password
for college and external participants, database-unique canonical email, no mandatory
college ID/email, public signup or forced first/reset password change. C18 email-only
login is active with complete database-unique canonical keys. Four
legacy fixtures received explicitly authorized organizer-assigned development
addresses, without mailbox/real-identity verification claims. C19 no-forced-change
policy is implemented. C17 session enforcement is retained (new login
invalidates old sessions, not physical-device binding). Recovery is organizer-
verified outside the app, with audited password reset and session revocation;
no email/token service. Emails stay private to owners and scoped organizers.
Teams, groups, special matches, general announcements, ratings and matchmaking are
**DEFERRED, not completed**. Keep upstream internal contest/scoring/organization
machinery; simplify templates and controls instead of rewriting the backend.
Approved UI direction keeps DMOJ horizontal navigation, centered content, compact
tables, sidebar styling and footer through existing templates, with no separate
frontend: [direction](docs/contracts/ui-direction.md).

Local CLI conversion and isolated judge
checks work. B01 runs the DMOJ-derived site with bounded admin/math asset fixes,
MariaDB and Redis locally at
http://127.0.0.1:8000/ with development accounts and a persistent disposable DB
volume; stop/start and actual Chromium authentication/admin boundaries passed.
B03 connects the pinned actual judge worker through native authenticated bridge
registration and verifies CPP11/14/17/20/23 capabilities and idle reconnect.
One private gaming-grid revision is now installed consistently in the website
and worker as `pv000000000000000001`; native worker advertisement is verified.
B06 renders the actual private statement with local math and scoped assets.
B07's real participant browser submission1 reached the native worker and returned
103 AC /103 points, with matching callbacks, stored rows and displayed verdict.
B08/B09 added real participant WA/CE/RTE/TLE submissions2–5 with matching
worker/callback/SQL/browser results and all309 executed case expectations.
B10/B11 now verify one private native contest with two temporary ordinary entrants,
separate official submissions and the fixed `cpjudge_icpc_v1` standings preset.
B12 confirms completed-result persistence through supported stop/start, unchanged
credentials/standings, native worker reconnect and new browser submission12 AC on103
cases. **Phase B / M1 COMPLETE — PASS** for this scoped local proof; interrupted
judging recovery remains untested. The original 111 MiB Polygon package now passes
the scoped local import-to-judging flow below. E09–E15 focused acceptance remains
preserved; A09's isolated services remain removed.

`Polygon ZIP → local strict adapter → pinned PCC model/writer → corrected DMOJ
problem files → installed probe copy → DMOJ CLI in Docker → logs/report`.
The browser/backend/database/bridge/worker/result route passed for one private
CPP23 reference plus WA/CE/RTE/TLE probes; the private two-entrant contest/standings
route now passes B10/B11. Broader contest lifecycle enforcement remains untested.
Convert on problem import/revision, not on each participant submission.

| Path/function | Current role |
| --- | --- |
| `local-packages/gaming-grid.zip` | Private real export; `build/` and `local-packages/` are ignored. |
| `compat/convert.py`: `upstream()`, `extract()`, `read()`, `convert()` | Validate pinned checkout/archive/metadata; construct PCC IR; call external `runner/package_adapters.py:write_dmoj()`; correct units/standards and preserve assets. |
| `tools/make_fixtures.py:build()`, `fixtures/` | Reproducible synthetic groups/multiple/tokens packages and licensed testlib. |
| `build/<run>/converted-N/<slug>/` | `init.yml`, `data.zip`, checker/header, attachments and sample sidecars; sibling ZIP/metadata/statement/conversion report. |
| `tools/pipeline.py:main()`, `tools/install_judge_tests.py:install()` | Copy to `problems/<slug>/`; add solution probes and submission time/memory; optional actual judging. Sorted fixture indices: groups 0, multiple 1, tokens 2; real 3. |
| `Dockerfile.judge`, `tools/judge-entry.sh`, `tools/runtime_metadata.py` | Pinned runtime/dependencies; unprivileged networkless container invokes official `dmoj-cli test`. A worker is an execution role; a container is its running environment, not a complete security boundary. |
| `tools/verify_install.py:verify()`, `tests/`, `tools/judge_results.py:summarize()` | Byte/configuration checks and complete observed-verdict validation; the parser does not decide answer correctness. |

## Current handoff — original Polygon ZIP import capacity (2026-11-02)

- **VERIFIED for the complete original package in the local site and isolated judge.** Unchanged 115,451,984-byte ZIP (261 entries, 247,507,278 expanded bytes) uploaded through Chromium author UI; job58 converted in 25.24s, previewed 103 tests and statement, and published immutable private version3 (`pv900000000000000003`). Native installation and signed CPP23 readiness passed. Original reference probe32 and participant submission33 each judged AC on all 103 cases; known-wrong participant submission34 judged 55 WA / 48 AC. Browser standings: accepted entrant 1 solved / 162s / rank1, wrong entrant 0 solved. Temporary contest `icap111a`, existing accounts and explicitly labelled temporary entrants only. [Concise summary, exact limits/checks/resource observations](reports/import-capacity-1/README.md); private inputs, browser scripts and raw results remain ignored in `build/import-capacity-1/`.
- Bounded configured ceilings: ZIP 128 MiB, multipart body ZIP+64 KiB, 1024 entries, 128 MiB/member, 320 MiB expanded, ratio100; upload temp-memory threshold1 MiB with private-disk streaming; converter 1.5 GiB address space/480s CPU/384 MiB output file/600s wall and solo concurrency1; conversion requires 2 GiB free, upload and publication retain 512 MiB reserves. Boundary/body/expansion/cleanup/privacy focused checks passed. No migrations; supported stop/start applied final settings without changing stored results or sandbox. No peak-memory, load, production deployment or crash-recovery claim. No F/G work, commit or push.
- **Next:** stop at this task boundary. H03's broader combined acceptance and college-server operational checks remain separate pending tasks; do not infer them from this package-specific local proof.

## Previous handoff — E09–E15 local acceptance (2026-11-02)

- **E09–E15 COMPLETE for scoped local checks.** Native same-key retry after discarding the first response returned submission30 twice, one receipt; real worker judged it AC3/3 on stored cases1–3. With Ace blocked, the plain textarea made submission31, also stored AC3/3 with one receipt. Browser direct/result/list/source/case/poll routes, interrupted poll, refresh/re-login, revoked session, removed entrant, keyboard filter, Ace failure/draft, blank-source validation, 375/640px widths and CSS 200% zoom passed. Prior B08/B09 failure verdicts remain the actual WA/CE/RTE/TLE evidence.
- Small fixes: native source textarea fallback when Ace fails; stored case numbering and explicit skipped label; list empty message and keyboard submit button; scoped tab/focus/width styles. Eight focused integration tests passed (pagination uses 52 constructed test-DB rows; skipped/no-worker/queued states are isolated, not new live worker outages). [One E09–E15 summary, commands and manual steps](reports/e09-e15-1/README.md).
- Temporary `eaccept1` submissions27–31 were created during browser test iterations and final fallback acceptance; each is an actual separate AC3/3 submission with its own receipt. Existing passwords, scoring, worker keys, sandbox and earlier submissions were preserved. At this historical E boundary, the original **111 MiB Polygon ZIP was a separate unresolved import-capacity task** under then-unchanged 32 MiB upload / 128 MiB conversion limits. No F/G work, commit or push.
- **Next:** only on request, the separate H03 combined journey or other explicitly authorized work; do not infer college-server readiness or original-package import support from this E check.

## Previous handoff — E01/E02/E04/E05/E17 acceptance (2026-11-02)

- **E01/E02/E04/E05/E17 COMPLETE — focused local browser PASS.** Anonymous HTML visits redirect to email login with a local return path; API request remains 401. Existing email-only/session protections pass 6 focused tests. One real native Ace submission, ID 26, is stored **AC 3/3 points and 3 cases** in temporary contest `eaccept1`; browser verdict and standings agree. Prior 25 submissions remain.
- Temporary development fixtures: four managed contests `eaccept1`, `eaccept2`, `eupcoming1`, `eended1`, one stock second-problem/language contest `estock1`, and four reserved `@e-accept.example.test` accounts. Credentials and browser scripts are ignored under `build/e01-e02-e04-e05-e17-1/acceptance/`. Existing contest settings, accounts/passwords, results, scoring and judge isolation were retained. The empty-home proof briefly excluded only the new test account from seven visible contests; three historical exclusion links were removed afterward.
- Browser checks: email login/local and unsafe return URL, eligible/empty home, upcoming/active/ended actions, register, statement, native editor/file load/submission/verdict/standings, current-user contest submissions, anonymous/API and removed-user denial, draft isolation across accounts in **one browser storage context**, contests and the two installed problems/languages; legacy language-only code never auto-restored. Same-problem two-language exercise was unavailable because enabled native languages are CPP17 on the approved synthetic version and CPP23 on the installed gaming-grid problem.
- [One E summary with commands, observations and limits](reports/e01-e02-e04-e05-e17-1/README.md). Stop before remaining E acceptance and operations work. No commit/push.

## Previous handoff — minimum native website review (2026-11-02)

- **Documentation review COMPLETE; implementation and new local journey PENDING.**
  Final user instruction “no implementation for now” controls this task. One
  agent inspected actual pinned native/custom source and retained acceptance;
  no application/service/schema/account/data changes or runtime tests.
- Reuse native Ace/problem/submission/cases/standings/polling and completed A–D
  guards. Small remaining gaps: authorized navigation/three tabs, native source
  file loading if absent, shared-browser saved-code isolation. Native rejudge
  exists but is policy-blocked; bounded history/replacement/finalization/export
  checks remain pending. Custom work only for demonstrated gaps.
- Plan/dependencies now defer Monaco/split layout/new draft sync/custom Run/extra
  languages/redesign. Internet independence and fixed capacity targets are not
  local-release prerequisites. Logo missing but nonblocking. Separate production,
  campus network, backup/restore, worker recovery and representative load checklist.
- [One summary: inspected code/results, URLs, manual steps, blockers and server checklist](reports/minimum-native-review-1/README.md).
  Commands: source/status reads and site HEAD pin exit0; corrected exploratory
  missing paths exit1/2; `python3 -B /tmp/cpjudge_minimum_check.py` and
  `git diff --check` exit0. No new conversion/judging/browser PASS claimed.
- **Next:** when implementation is requested, E01 → E02/E17 → native editor/
  saved-code/privacy checks → actual combined H03 browser journey, with bounded
  F operations follow-up. Follow [current dependency order](MVP_DEPENDENCIES.md).
  Preserve expired fixtures and all prior accounts/hashes/imports/results/audits;
  backup privately before any migration. No commit/push/public deployment.

## Previous handoff — D13 / retained Phase D closure (2026-10-30)

- **D13 COMPLETE — local PASS; retained Phase D COMPLETE**, one sequential agent.
  Labelled owner/scoped-admin preview and private persisted author tests reuse
  native submissions and C11 exact-version isolated judging. Archived receipts
  have no official contest/participation/scoring row. Server-side conflicts and
  native/direct guards reject crafted ranked author attempts; participant clocks
  and access remain enforced.
- **Checks:**6 focused permission/binding/scoring checks and11 relevant entry/time/
  receipt regressions pass,0 skips. Actual Chromium submissions24 **CPP17 AC3/3**
  and25 **WA3/3**, one dispatch each; all6 callbacks/cases agree with SQL. Private
  verdicts survive new login. Participant/test/deadline/removal bypasses denied;
  official standings, counts and solve statistics unchanged.
- **Preservation:** private full backup before additive0012;72 model sets /2220
  prior non-session rows preserved. Accounts/hashes/results/imports/audits,
  native problem aggregates, worker image/config/sandbox retained. Prior native
  navigation pointers restored; schema and whitespace checks exit0.
- [One summary, exact commands, evidence and manual steps](reports/phase-d-d13-1/README.md).
  Preview: http://127.0.0.1:8000/author/contests/d07local2/preview/.
- **STOP before Phase E.** D10/D12/D14/D15 remain deferred. No new import/probe/
  participant judging rerun, capacity/crash/production claim, commit or push.
  Historical stop boundary; current documentation-only simplification is above. No D13 blocker.

## Previous handoff — D07–D09/D11 (2026-10-30)

- **D07–D09 and D11 COMPLETE — local PASS**, one sequential agent. Idempotent
  pre-start registration/withdrawal, late entry/common end, private scoped roster,
  reasoned/audited removal and DQ. Removal retains rank; DQ excludes it. Native
  participations/scorer retained; explicit atomic submission receipts prevent
  deadline/practice/context bypass and preserve admitted work after revocation.
- **Checks:** 10 focused MariaDB/HTTP boundary/race/privacy checks and 12 relevant
  author/session regressions pass,0 skips. Actual Chromium registration/withdrawal/
  late entry/removal/DQ and denied native/direct/poll routes pass. Exactly new
  submission23 CPP17 **AC3/3**, one receipt; DQ retains its solved point as evidence,
  remaining entrant becomes rank1. No conversion/new probe/import rerun.
- **Preservation:** fresh private backup before additive migration0011; 70 prior
  model sets/2138 non-session rows checked. Accounts/passwords/imports/old results
  and audits retained; expected native problem aggregates reflect new submission.
  Native navigation restored, runtime content/sandbox preserved, schema/whitespace pass.
- [One summary, commands, limitations and manual steps](reports/phase-d-d07-d11-1/README.md).
  Author page: http://127.0.0.1:8000/author/contests/; local accepted roster:
  http://127.0.0.1:8000/contest/d07local2/roster. Initial task-owned expired fixture
  and failed browser attempts preserved; no live schedule reset/extension.
- **Historical stop before D13** (subsequently completed above). D10/D12/D14/D15 deferred. No capacity,
  interrupted-job recovery, restoration UI, configurable registration windows or
  full participant-workspace claim. No commit/push. Supervised in-person scope retained.

## Previous handoff — D01–D06 (2026-10-30)

- **D01–D06 COMPLETE — local PASS**, one sequential agent. Scoped private draft
  create/edit, immutable version selection/label/order, aware schedule/countdown,
  provisioned eligibility, fixed scoring/language/feedback rules, preview and fresh
  worker/probe-gated publication. [One summary/commands/manual steps](reports/phase-d-d01-d06-1/README.md).
- **Checks:** 8 focused DB/HTTP tests, 0 skips; actual Chromium create/edit/preview/
  publish and denied participant/unrelated management/draft/pre-start access;
  actual stale/auth/missing-problem readiness rejection. Exact [S,E) constructed
  receipt checks pass; no new conversion or judging. Published local fixture `d01local1`.
- **Preservation:** private full backup before additive migration0010; 68 prior
  model sets / 2098 non-session rows checked. Accounts/hashes/results/imports and
  sandbox retained; semantic runtime advertisements retained across idle reconnect.
- **Scope:** supervised, in-person. D14 deferred and removed from required edges;
  no archive/practice/editorials/virtual/announcement MVP navigation. Native shell
  retained. Author URL: http://127.0.0.1:8000/author/contests/.
- **Historical D01–D06 boundary:** registration/removal was blocked then; the
  subsequent D07–D09/D11 request is complete above. D13, E workspace/home completion,
  production/capacity/LAN/recovery remain later tasks. No commit/push.

## Previous handoff — C18 cutover / Phase C local closure (2026-10-30)

- **C18 COMPLETE — local PASS; Phase C COMPLETE for retained local gates.** All17
  C01–C13/C16–C19 gates plus same-version integrated acceptance have evidence;
  C14/C15 remain deferred. [One summary/commands/recovery](reports/phase-c-c18-cutover-1/README.md).
- Four user-authorized development-fixture addresses applied through existing
  check/apply workflow, audited as organizer-assigned, **not verified mailboxes or
  real participant identities**.10 canonical keys,0 unresolved. Email-only mode ON;
  ordinary username login rejected, email/password admin access works.
- **Checks:**15 focused native tests pass,0 skips; actual4-account email/username/
  admin/no-forced-change/privacy/history checks and cutover/replacement stale
  read/POST/poll/logout revocation pass. Local administrator recovery/re-cutover
  rehearsed in isolation; protected live recovery input prepared without rollback.
- **Preservation:** fresh private readable backups;68 model sets/2089 prior
  non-session rows checked. All10 existing password hashes, account IDs/usernames,
  college history/roles, old submissions/cases/source/standings/audits preserved.
  Exactly4 email/key assignments,3 additive identity rows and6 audits; no password
  reset/change, new judging, migration or identity merge. Deployed source/schema/
  whitespace pass. [Preservation](reports/phase-c-c18-cutover-1/preservation.json).
- **Integrated evidence reused:** version2/probe17→official20 WA3/21 AC3/22 AC3;
  Q1 solved/510s/rank1, P1 solved/1699s/rank2. No conversion/probe/judging rerun.
  [Same-version proof](reports/phase-c-integrated-1/README.md).
- **Historical C18 boundary:** no Phase D was authorized by that closure; the later explicit D01–D06 request is recorded above. No commit or push. Full MVP/M2, deployment/capacity/LAN,
  recovery and original111MiB package validation remain later work; unchanged
  32MiB upload/128MiB conversion limits. No mailbox/real-identity/production claim.
  One college server with separate authenticated isolated worker settings remains
  the intended deployment; remote access requires separate authorization.

## Task status and evidence

| Task | Status | Evidence |
| --- | --- | --- |
| Minimum native scope review | COMPLETE — documentation only; implementation/journey pending | [Source findings, classification, URLs/manual steps and separate server checklist](reports/minimum-native-review-1/README.md); plan/dependencies updated, no runtime acceptance inferred. |
| D13 author preview/tests; retained Phase D closure | COMPLETE — local PASS; stop before Phase E | [One summary,17 checks, actual AC3/WA3, unchanged official statistics/preservation](reports/phase-d-d13-1/README.md). |
| D07–D09/D11 registration, roster and removal/DQ | COMPLETE — local PASS; historical stop before D13 | [Single summary,22 checks, actual browser/AC3/standings/preservation](reports/phase-d-d07-d11-1/README.md). |
| D01–D06 scoped contest workflow | COMPLETE — local PASS; subsequent registration bundle recorded separately | [Single summary, actual browser/readiness/preservation, exact commands](reports/phase-d-d01-d06-1/README.md). |
| A01 repository orientation | COMPLETE; useful facts consolidated here; inspection did not rerun judging | This inventory; [compatibility report](reports/compatibility.md); [recorded judge evidence](reports/judging-docker-resume.json). |
| Prior isolated judge milestone | PASS, historical run; not an A03 reproduction | 18 probes / 454 case records, 11 unit tests; real reference 103 AC, wrong 55 WA / 48 AC, runtime 103 RTE, timeout 103 TLE. Private raw run: `build/judging-milestone-docker-resume-3/`. |
| A02 converter reproduction | COMPLETE — PASS; judging NOT TESTED | [A02 summary/commands](reports/a02-converter-1/README.md), [evidence](reports/a02-converter-1/evidence.json), [preservation](reports/a02-converter-1/preservation.json), [metadata](reports/a02-converter-1/metadata.json). |
| A03 isolated judge reproduction | COMPLETE — PASS, independently reviewed | [A03 report/commands](reports/a03-judge-1/README.md), [evidence](reports/a03-judge-1/evidence.json), [review](reports/a03-judge-1/review.json), [scores](reports/a03-judge-1/scores.json), [live sandbox](reports/a03-judge-1/sandbox.json). |
| A04 website foundation | COMPLETE — source inspection only; setup NOT TESTED | [A04 report](reports/a04-site-foundation-1/README.md), [exact source/docs pins](reports/a04-site-foundation-1/source-pin.json), [environment/support](reports/a04-site-foundation-1/support-sources.json). |
| A05 upstream feature map | COMPLETE — source mapping only | [20-feature table](reports/a05-feature-map-1/README.md), [source hashes and classifications](reports/a05-feature-map-1/features.json), [inspection checks](reports/a05-feature-map-1/inspection-checks.json). No feature runtime tests or implementation. |
| A09 maintainable website stack | COMPLETE — PASS for supported-stack startup; migration-state diagnostic remains failed | [Report/setup](reports/a09-site-1/README.md), [versions/results](reports/a09-site-1/evidence.json), [commands/exits](reports/a09-site-1/commands.json), [preservation](reports/a09-site-1/preservation.json). No website-to-judge test. |
| A06 Permissions/identity/session contract | COMPLETE — Specified scope, canonical IDs, private email/source/tests, unranked conflicts and single-active-session generation policy; enforcement NOT TESTED | [Permissions/identity/session contract](docs/contracts/permissions.md); [audit/command exit 0](reports/phase-a-close-1/checks-A06.json). |
| A07 Contest lifecycle and fixed rules | COMPLETE — Specified registration, [S,E) receipt admission, late entry, removal vs DQ, penalties/ties and expected examples; enforcement NOT TESTED | [Contest lifecycle and fixed rules](docs/contracts/contest-rules.md); [audit/command exit 0](reports/phase-a-close-1/checks-A07.json). |
| A08 Project instructions/resume workflow | COMPLETE — Commands, evidence distinctions, task ownership and resume workflow documented; documentation audit only | [Project instructions/resume workflow](AGENTS.md); [audit/command exit 0](reports/phase-a-close-1/checks-A08.json). |
| A10 Native scoring/clock mapping | COMPLETE — Source mapping and isolated native-method probes PASS; common late-entry clock verified; scoring/deadline adaptations specified; SQL/site integration NOT TESTED | [Native scoring/clock mapping](reports/a10-native-1/README.md); [audit/command exit 0](reports/phase-a-close-1/checks-A10.json). |
| A11 Immutable versions/compatible dispatch | COMPLETE — Source/path/cache and 6 native selection checks PASS; immutable native codes, external readiness receipts and attempt mapping specified; live routing NOT TESTED | [Immutable versions/compatible dispatch](reports/a11-dispatch-1/README.md); [audit/command exit 0](reports/phase-a-close-1/checks-A11.json). |
| A12 Custom-input Run route | COMPLETE — Source-grounded separate executor adapter, isolation/limits/quotas/result contract specified; actual custom execution NOT TESTED | [Custom-input Run route](reports/a12-run-1/README.md); [audit/command exit 0](reports/phase-a-close-1/checks-A12.json). |
| B01 local website/database baseline | COMPLETE — PASS; 202 genuine migrations, consistency/dependencies/static checks, 9 real Chromium journeys, stop/start and independent review; warnings/4 scoped JS errors retained | [Setup/commands](reports/b01-site-1/README.md), [result](reports/b01-site-1/result.json), [review](reports/b01-site-1/review.json), [preservation](reports/b01-site-1/preservation.json). |
| B01 bounded follow-up / UI direction | COMPLETE — PASS; real admin loading/Actions integration, pinned local MathJax with strict rendered checks, both static conflicts resolved, read-only verification and explicit reset; original users/data/reports preserved | [Report/commands](reports/b01-followup-1/README.md), [result](reports/b01-followup-1/result.json), [runtime](reports/b01-followup-1/runtime-final.json), [preservation](reports/b01-followup-1/preservation.json), [approved UI](docs/contracts/ui-direction.md). |
| B02 native local services | COMPLETE — real bridge/Celery/events, noop task, exact WS/HTTP diagnostic delivery, no-worker bridge probe, restart/idempotent-start and Chromium smokes passed; final review in report | [B02 evidence/commands](reports/b02-services-1/README.md), [runtime preservation](reports/b02-services-1/runtime-preservation.json), [review](reports/b02-services-1/review.json). |
| B03 authenticated local worker | COMPLETE — PASS; pinned actual worker/GCC16.2.0, native CPP11/14/17/20/23 self-tests/capabilities, real online/offline/reconnect, idempotent/full lifecycle, submitted socket/config denials; existing rows/overlay/math/migrations/pins preserved; independent review PASS | [B03 report/commands](reports/b03-worker-1/README.md), [lifecycle](reports/b03-worker-1/acceptance.json), [review](reports/b03-worker-1/review.json), [evidence audit](reports/b03-worker-1/evidence-audit.json). |
| B04 native problem installation mapping | COMPLETE — PASS for source/package mapping; 2s/262144KiB, CPP23 bridged/testlib, 103 ordered one-point cases, private immutable native revision specified; judging NOT TESTED | [Mapping/source evidence](reports/b04-installation-1/README.md), [values/hashes](reports/b04-installation-1/mapping.json). `.venv/bin/python -B deploy/site-local/problem_install.py plan` exited0. |
| B05 real private problem installation | COMPLETE — PASS; 103 ordered source/worker pairs, checker/header/sample/15 assets, CPP23/limits, immutable manifest/read-only data, safe repeat/collision checks, real native advertisement,696 anonymous/participant HTTP denials; no submission | [Installation/commands/limits](reports/b05-problem-1/README.md), [independent review](reports/b05-problem-1/review.json), [saved-evidence audit](reports/b05-problem-1/evidence-audit.json). |
| B06 real private statement | COMPLETE — PASS for actual Chromium source/constraints/sample/30 local-math comparison, strict receipt-bound HTML/CSS/TeX handling, scoped participant access and219 hidden-data denials; judge data/limits unchanged; no submission | [Report/commands](reports/b06-statement-1/README.md), [presentation hashes](reports/b06-statement-1/presentation.json), fresh browser/preservation evidence in report. |
| B07 first actual browser submission | COMPLETE — PASS; native participant form→bridge→real worker, submission1 CPP23, observed2s/262144KiB,103 actual AC1/1 cases, native callbacks/SQL/browser verdict agree, scoped preservation;3 compiler warnings retained | [Report/commands](reports/b07-submission-1/README.md), [stored result](reports/b07-submission-1/result.json), [actual cases](reports/b07-submission-1/cases.json), [native trace](reports/b07-submission-1/native-trace.json). |
| B08 WA/CE website probes | COMPLETE — PASS; native participant submissions2 WA (55 WA/48 AC) and3 CE (zero executed cases), worker/callback/SQL/browser agreement | [Results/commands](reports/b08-b09-probes-1/README.md). |
| B09 RTE/TLE and case details | COMPLETE — PASS; submissions4 RTE and5 TLE,103 cases each; callback/SQL/browser numbering/status/points agree; zero SC | [Results/commands/limitations](reports/b08-b09-probes-1/README.md), [preservation](reports/b08-b09-probes-1/preserve.json). |
| B10 private individual contest | COMPLETE — PASS; temporary b10b11local1,2 ordinary allowlisted accounts, browser denials/join/problem visibility, separate WA submissions6/7; common server start/end | [Bundle evidence](reports/b10-b11-contest-1/README.md); existing problem remains private. |
| B11 standings comparison | COMPLETE — PASS; fixed native preset corrects observed hidden tiebreaker/stable order; both entrants1 solved/2161s/rank1, CE excluded, later WA ignored;18 focused checks | [Expected/actual table, commands, limits](reports/b10-b11-contest-1/README.md), [preservation](reports/b10-b11-contest-1/preserve.json). |
| B12 completed-result restart persistence | COMPLETE — PASS; supported full stop/start,4 browser credential sets,11 existing submissions/927 cases unchanged, native worker reconnect, new submission12 AC103 cases and correct standings | [Short summary/commands/limits](reports/b12-restart-1/README.md), [acceptance](reports/b12-restart-1/acceptance.json), [preservation](reports/b12-restart-1/final-preservation.json). |
| Phase B / M1 | COMPLETE — PASS for B01–B12's scoped local website-to-judge gates; full MVP remains future work | Existing B01–B11 evidence above plus B12; no historical judging or unrelated audits repeated. |
| CPJudge MVP scope revision | COMPLETE — documentation only; no feature task completed | [Plan](SecureExam-Implementation-Plan.md), [MVP dependencies/deferred work](MVP_DEPENDENCIES.md), [documentation checks/preservation](reports/cpjudge-scope-1/checks.json). Existing milestones retained. |
| Single-server / email MVP consolidation (2026-10-30) | COMPLETE — documentation only; C18/C19 were then pending, existing completions preserved | Current plan, MVP_DEPENDENCIES.md and A06/A07 contracts; 114-task graph/91-task selected closure and 172 local links checked, exit0; `git diff --check` exit0. No runtime test. |
| C11 exact immutable version/hash readiness | COMPLETE — local PASS; 27 focused tests, one actual browser submission16 AC103/103 after mismatch/queue/reconnect; no C13 probe | [One summary/checks/commands/limitations](reports/phase-c-c11-1/README.md), [actual results](reports/phase-c-c11-1/live.json), [preservation](reports/phase-c-c11-1/preservation.json).64 model sets/1849 prior rows preserved except normal native activity; no migration/dependency/credential/sandbox change. |
| Same-version integrated acceptance | COMPLETE — local PASS; job24/attempt2/version2→accepted private probe17→official20 WA3/21 AC3/22 AC3→manual/browser/SQL standings; hashes/passwords/history preserved | [Summary/commands/mapping workflow](reports/phase-c-integrated-1/README.md), [proof](reports/phase-c-integrated-1/proof.json). C18 cutover now passes; historical integration evidence retained. |
| Phase C retained local gates | COMPLETE — C01–C13/C16–C19 and same-version integrated smoke accepted; C14/C15 deferred | [Acceptance inventory/limits](reports/phase-c-c18-cutover-1/README.md). Not M2/full MVP or production readiness. |
| C19 no forced password change | COMPLETE — independent local PASS; provision/reset/voluntary change/browser revocation and C17 regressions; C18 cutover now complete | [Bundle evidence](reports/phase-c-c13-identity-1/README.md), [browser](reports/phase-c-c13-identity-1/c19-browser.json). No original password reset. |
| C18 personal-email login | COMPLETE — local PASS; four authorized development assignments,10 unique keys, email-only cutover/admin access, username rejection, session revocation and local recovery; hashes/history preserved | [Closure summary](reports/phase-c-c18-cutover-1/README.md), [browser](reports/phase-c-c18-cutover-1/browser-after.json). No mailbox verification or password change. |
| C13 restricted problem probe | COMPLETE — local PASS;29 focused checks, browser AC3/WA3, private/version/source/runtime binding and native worker; no participant publication | [Bundle summary](reports/phase-c-c13-identity-1/README.md), [actual execution](reports/phase-c-c13-identity-1/c13-live.json). |
| C12 remaining upload acceptance | COMPLETE — local PASS; real DB/HTTP concurrency, published Chromium re-upload and owner isolation; existing implementation reused | [One summary/commands/limits](reports/phase-c-c12-1/README.md), [browser](reports/phase-c-c12-1/browser.json), [preservation](reports/phase-c-c12-1/preservation.json). Three focused tests; zero new orphan files; no prior credentials/results/history/private-file change. |

**Previous implementation task: C10 COMPLETE — local private-publication PASS, one agent.**
Scoped owner/current-attempt/CSRF publication reuses C09 sanitization and B04/B05
native mapping/manifest/immutable installer. Durable intent → private fsynced
no-replace installation → atomic native Problem/version/audit supports recovery
without overwriting older versions. Only this POST releases C17's outer request
transaction; session/account/scope are rechecked under account locks at each
admission/finalization.25 focused native tests +6 installer checks and final
Chromium publication pass, including concurrency, filesystem/DB failures, actual
post-rename process exit/recovery, revoked/replaced sessions and protected routes.
Import24/attempt2 is private `pv900000000000000002`,0.5s/65536KiB,CPP17 checker,
3 tests/3 points/1 sample; native/files agree. Earlier private version1 remains
usable. No contest assignment/public visibility/submission languages; HTTP and
native judge admission remain blocked pending C11/C13.63models/1776 prior rows and
container/worker configuration preserved; one natively expired browser contest
pointer restored to baseline. Fresh readable backup preceded migration0006;
restore/full power-loss/container recreation untested. Original111MiB ZIP remains
over unchanged limits; **no full-package verification**. [One C10 summary,
commands/exits/results/limits/recovery](reports/phase-c-c10-1/README.md).
**Historical C10 boundary: stopped before C11 readiness and C13 probes; C11 is now complete above.**
No judging, commit or push.

**Previous task: C09 COMPLETE — local private-preview PASS.** Owner/scoped-author
current-success/digest checks protect sanitized statements and decoded/re-encoded
PNG assets; explicit notices and B06 formatting/local math retained.39 focused
checks and Chromium raw-response/network-attempt/DOM/access/traversal/spoof/
cross-import/retry checks passed; actual24 refreshed to attempt2 and rejected old
assets. The unchanged real statement renders30 equations/sections/samples in a
supported synthetic conversion, **not full acceptance of the111MiB original**.
63models/1762 prior rows and containers preserved; only HTTP reloaded. [C09 summary,
commands and limitations](reports/phase-c-c09-1/README.md).

**Previous task: C08 COMPLETE — local PASS.** Owner-only escaped persisted-output
compatibility preview shows identity/counts/units/checker standard/scoring/warnings
and fixed corrective guidance. Unknown metadata stays unverified; conversion,
judging and publication are distinct.28 focused checks and Chromium conversion/
refresh/unsupported/scoping/injection/stale-state checks passed; displayed values
agree with report/init.63models/1756 prior rows and containers preserved, no migration
or judging. [Preserved C08 summary/evidence](reports/phase-c-c08-1/README.md).

**Phase C checkpoint1 COMPLETE — integrated local PASS**, sequential owner.
C01–C04/C16/C17 enabled on actual site; [one summary/acceptance/commands/rollback/exposure](reports/phase-c-checkpoint1-1/README.md), including the completed key/session remediation.
Native auth/profile/scoped admin/routes/source/files/exports and real Celery guards,
audited college-ID correction, forced changes and generation/admission/poll checks
pass:22 native tests plus3 targeted checks (overlap recorded), real Chromium role/
A–B email isolation, legacy unchanged-password login, recovery/correction/session
replacement and known-source/channel-ID denials. Unscoped legacy management APIs/
tasks are disabled; authenticated native-widget polling replaces the stopped daemon;
ports9995/9996 stay closed through supported startup. No guessed IDs or old resets.
Fresh private readable backup preceded real cpjudge0001–0004 migrations; live
PBKDF2, no test settings. Original account hashes/contest/source/results and worker
image/config/sandbox/immutable files preserved (56-model comparison; only the
authorized worker auth_key changed). New native submission14 AC103/103 matches
SQL/callback/browser and36 authenticated polls.
Failed test13 remains native IE/zero cases: dispatch-before-commit defect fixed
with on-commit dispatch and rollback regression; no crash-recovery claim.
Temporary elevated acceptance account disabled; named private c1livea/b fixtures
and results retained. Exposure remediation: old worker key rejected by a real
bridge handshake; new private key/config/registration/DB values agree and worker
reconnected. All23 stored sessions removed and six identity generations revoked;
captured old cookie returns401, while an existing legacy password still logs in.
Fresh private pre-rotation backup readback passed; file mode0600. Browser submission15
after rotation returned AC103/103 with22 authorized polls. Existing passwords,
college IDs, results and sandbox preserved. Earlier transcript cannot be deleted
from this workspace; it may still contain password hashes/private data, and the old
key may remain in restricted historical backups. No account passwords reset.
Legacy `manage.py status`'s anonymous `/status/` probe currently receives401 from
the route gate; direct native bridge state plus browser judgment verified worker.
Rollback documented/syntax checked, not executed.

**C05 COMPLETE — PASS for local single-ZIP upload integration.** Reused the
existing owner-associated ImportJob/private upload core and bounded ZIP preflight;
added native DMOJ form, owner confirmation/download, contest scope, CSRF, streamed
byte cap and cleanup on errors. Actual author Chromium upload/refresh/download
passed; eight focused tests cover role isolation, scoped admin access, missing/
invalid CSRF, malformed/multiple files, actual byte counting with missing or
understated length, and cleanup. Browser limits: 32MiB; public/static/media access
denied. One task-owned C1LIVEA upload fixture remains private; account passwords,
prior submissions/results and worker configuration remain unchanged. No migration
was needed. [C05 summary, actual checks, reproduction and page URL](reports/phase-c-c05-1/README.md).
C05 code review fixed unbounded draining/total-body reads, collision cleanup that
could delete an existing file, and storage-path error disclosure. Eight focused
tests plus live browser/storage and prior-data/worker preservation checks pass.
Crash/outer-transaction rollback orphan reconciliation and aggregate quotas remain
untested/unimplemented. The local WSGI server returns411 for unframed/chunked requests it cannot delimit;
terminated streams are counted by the upload handler. No conversion, extraction,
job queue, publication or execution was started. **Stopped after C05.** C07–C09
remain partial, C10/C11/C13/C14 pending, C15 DEFERRED. No Phase D/commit/push.

**C06 COMPLETE — PASS for local extraction-service integration.** Reused the strict
extractor and pinned Polygon metadata reader. Added an authorized extraction-only
context for owned stored ZIPs: digest check, fresh private staging, bounded actual
extraction, safe errors and attempt-only cleanup. Existing C05 HTTP upload reached
this service and was safely rejected for missing Polygon metadata, with original
file/record/other jobs preserved. Supported-package success is service-level;
no website extraction action or background queue was enabled. Final checks:
18 archive tests, 6 converter regressions, 19 native service/C05/core tests pass.
[One C06 summary, commands and actual website/service distinction](reports/phase-c-c06-1/README.md).
No migration or service restart. C07 dependency/queue/recovery integration remains
pending. **Stopped before C07.**

**C07 COMPLETE — local queued conversion PASS.** Reused ImportJob/C06/strict
converter and real Celery; owner-scoped CSRF Convert/Retry and persisted status/
attempt/error are live. Admission publishes after commit; token/row locks fence
concurrent requests, duplicate delivery and stale completion. Trusted child has
wall/CPU/memory/file limits; inherited global lock limits conversion concurrency1.
Fresh readable private backup preceded additive migration0005; restore untested.
Final12 focused checks passed; actual browser job13 queued→running→succeeded and
refresh persisted. Unsupported8/malformed9 failed safely. Real broker refusal12
and Celery interruption10 both recovered to succeeded attempt2 through retry;
interruption used a task-owned accelerated lease while waiting for the global lock.
Original passwords/IDs/results/keys preserved (63models/1749rows), and native judge
container/config/sandbox/start time unchanged. Reconcile expired queued300s/running
180s via owned status page or local `manage.py reconcile_imports`; unattended jobs
require the documented operator command (no periodic scheduler). Aggregate storage
quotas/full-host-crash/capacity behavior remain limitations. [One C07 summary and
actual checks](reports/phase-c-c07-1/README.md). Success is conversion only.
**Stopped before C08**, publication and judging probes. No commit/push.

**Historical B10/B11 bundle: COMPLETE — PASS**, one agent. Private `b10b11local1`,
temporary `b10tmpa`/`b10tmpb`; browser access denials/join/statement and separate
submissions6–11 passed. Server receipts yield961 elapsed seconds+1200 for one prior
WA each: both1 solved/2161s/rank1, stable B/A entry-ID order. CE8 and post-AC WA11
add no penalty. [One summary/table and exact commands](reports/b10-b11-contest-1/README.md).
Observed stock rank1,2 corrected by registered `cpjudge_icpc_v1`, scoped full-AC
credit/ranking hooks and metadata migration0154 (203 applied; consistency exit0).
Native code reload used idle guards; no AC rejudge/resubmission. Final browser and
stored/manual standings agree;515 actual cases agree with callbacks; CE ran no cases.
18 focused checks pass, including rollback-only SQL ordering and constructed1,1,3/
authoritative-replacement cases; these are separate from actual judging. Preservation
passes across88 models, existing accounts/passwords/submissions/problem files and
worker config/images/sandbox. Setup/CE/pair/install/checks/after/collect/standings/
preserve final exits0; failed driver attempts/logs retained under ignored build/.
No blocker; temporary fixture retained, credentials ignored. Exact deadlines/races,
full lifecycle policies, operational rejudge/recovery/load remain untested.
B12 later completed above. No redesign/commit/push in this historical bundle.

**Historical B08/B09 bundle:** COMPLETE — PASS; [results, commands, limitations](reports/b08-b09-probes-1/README.md).
Submissions2–5 WA/CE/RTE/TLE matched309 executed case expectations. CE executed
no cases. Existing data/configuration preserved; no application fix or AC rerun.

**Historical B06/B07 bundle:** COMPLETE — PASS for their scoped checks.
[B06 source/rendering/access](reports/b06-statement-1/README.md),
[B07 actual execution and exact commands/exits](reports/b07-submission-1/README.md).
Private problem `pv000000000000000001` renders30 source-matching local equations,
constraints/samples; only selected ordinary participant tester has access.
Native browser submission **1: AC,103/103** using CPP23 on cpjudge-local-worker.
Observed sent limits2.0s/262144KiB; all103 native worker callbacks/DB cases are AC1/1
and participant display agrees. No CLI substitute or direct verdict writes.
Three compiler warnings retained privately; no warning-free claim. Snapshot,
instrument, final submit/results/preserve-submit exited0; failed driver attempts
created no submission. Precise preservation permits only native login/access,
one Submission/Source+103 cases and native problem AC stats; existing passwords,
pins, worker config and immutable data remain unchanged. Passive bridge logging
is a documented observer overlay, not a protocol/result change. B06/B07 independent
reviews PASS; [final evidence audit](reports/b07-submission-1/evidence-audit.json)
PASS. `.venv/bin/python -B reports/b07-submission-1/verify_evidence.py` and
`git diff --check` exited0; historical evidence/pins and private credential exclusion
verified. B08/B09 now continue below that historical boundary.
B10/B11 later verify the scoped private contest/standings route; full readiness/recovery remain untested.

**Historical B04/B05 acceptance:** COMPLETE — PASS; independent reviews PASS.
[B04 mapping/source limits](reports/b04-installation-1/README.md),
[B05 operator procedure/evidence](reports/b05-problem-1/README.md).
Private gaming-grid revision1 / native `pv000000000000000001` (PK1) is installed;
full manifest SHA256 `7e7b7ec333912da774b066e821eae4c2cb9cb9426ea3417320352d128b5dcf90`.
Source2000ms/268435456bytes → site/init2s/262144KiB → expected request2s/262144KiB;
CPP23 only, checker bridged/testlib CPP23,103 active one-point cases, standalone
points103/partial=True; contest scoring remains separate/unimplemented.
Actual worker recognizes the code; repeat installation reuses row/files. All103
pairs, checker/header, sample and15 assets match source; hidden data/source/static
routes denied for anonymous and ordinary participant. No programs submitted.
Operator snapshot/install/repeat/verify/privacy/cache cleanup/preserve and6 tests
exited0 in final runs; failed explorations retained. Accounts/passwords/sessions
and worker configuration preserved; diagnostic profile last_access restored to
recorded millisecond precision (original sub-millisecond value not provable).
No installation blocker. A11 verified boot-bound readiness/probe/dispatch gates,
actual emitted submission packets and judging were untested at the B05 boundary;
B06 was then next. Original B01–B03 reports/pins remain unchanged.
Final `.venv/bin/python -B reports/b05-problem-1/verify_evidence.py` and
`git diff --check` exited0: both reviewed hash sets, prior-file preservation,
private credential exclusion and ignored packages/data passed. Exact operator
commands/exits are in the B05 report/ledger; conversion was reused, judging not run.

**B03 historical acceptance:** COMPLETE — PASS; [evidence and exact commands/exits](reports/b03-worker-1/README.md).
Website/MariaDB/Redis/native bridge/Celery/events and `cpjudge-local-worker` are
running locally. Native authenticated handshake advertises five C++ executors
with major version16; real compiler full version16.2.0 and CPP23 `std::expected`
were verified separately. Native website/ORM offline→online transitions passed.
Zero problems were installed during B03; no website submissions judged then.
The manager handles worker last-on/first-off, serialized/idempotent, with SIGINT
cleanup (exit0, non-OOM). Bridge guard permits only the matched owned registration,
still refuses in-progress jobs/unknown judges; in-flight recovery remains untested.
Ordinary verify remains non-mutating and reports actual worker/runtime counts.
Prior B02 CORS/replay/production limitations remain; no B03 blocker.
`python3 -B deploy/site-local/b03.py acceptance`, final `stop`/`status`/`start`/`verify`,
ordinary `manage.py verify`, final `manage.py status`, and
`python3 -B reports/b03-worker-1/verify_evidence.py` exited 0; `git diff --check`
exited 0. Fresh commands/logs and failed explorations are retained in the B03 report.

**Historical B02 acceptance/status** (superseded runtime state by B03 above): B02 COMPLETE — PASS, independent review PASS; evidence recorded under
[reports/b02-services-1/](reports/b02-services-1/README.md). Latest read-only status
on 2026-10-29 before B03: website, DB, Redis, bridge, Celery and event daemon were **STOPPED**;
this does not invalidate the recorded B02 acceptance. See
[status reconciliation/commands](reports/b02-status-1/README.md). Native bridge
and Celery are configured inside the preserved website container, with the event
daemon in its own pinned Node container. Consumer ports 9996/9995
are localhost-only; bridge 9998/9999 are container-loopback and event sender9997
is private. No judge was enrolled during B02. Service readiness
is not evidence of successful judging/import/standings.

Real noop task and exact diagnostic event/ID delivery passed before/after restart;
repeated start keeps one bridge and worker. WS dependency updated to pinned 8.22.0
following a retained npm advisory; fresh audit has zero findings. B01 overlay,
all math assets, 0153 and 202 migrations remained exact during acceptance; passwords never reset.
Native startup had a zero-Judge/in-progress guard because upstream resets those
states; B03 replaced it with the owned-registration/idle guard above. Browser HTTP-poll CORS fallback and durable
event replay are unverified; production warnings stay visible. Prior reports and
user work are preserved. `python3 -B reports/b02-services-1/check_preservation.py`
exited 0; prior reports remain byte-identical and credentials are excluded.
Full deployment commands are in the B02 report.

B02 status reconciliation: `python3 -B reports/b02-status-1/verify.py` and
`git diff --check` exited 0; reviewed source/evidence hashes and the original
command-ledger prefix are intact. Read-only `manage.py status` exited 0 after
the sandbox's `sg` restriction required escalation. No runtime acceptance tests
were repeated; services were left stopped. [Fresh audit](reports/b02-status-1/audit.json).

Admin shortcuts use WPadmin's real jQuery; canonical Django bootstrap and native
Actions auto-initialization work on tested pages, with no stubs or swallowed
errors. MathJax 3.2.2 JS/extensions/fonts/license are local and pinned; native
profile and synthetic statement/preview render exactly three equations each,
including local color autoload. Browser checks have zero page errors. Static
sources are unique; site CSS retains its bytes in an explicit namespace.

Ordinary `verify` no longer loads fixtures, applies migrations or sets passwords;
all existing password hashes stay exact, including a changed test password.
Explicit password-only reset was separately tested with temporary accounts. Both
sets of temporary fixtures were removed; original users/profiles/domain counts
are exact. The 0153 fix and 202 consistent migrations remain unchanged. No B01
follow-up blocker; production/MariaDB warnings remain.
Final saved-evidence audit: `python3 -B reports/b01-followup-1/verify_evidence.py`
exited **0**; 332 original files checked, only seven authorized source/guidance
files changed; all original B01/A09/prior reports are byte-identical. Gravatar was blocked as
optional decoration; full-site offline/production readiness is not claimed.

Prior Phase A completed its specifications/source investigations; six shared-doc
snapshots and the 221-file closure baseline remain under `build/phase-a-close-1/`.
Its final documentation audit exited 0. B01's own baseline is 249 files under
`build/b01-site-1/`; converter/judge/fixtures/locks and prior reports are preserved.

Current decisions (2026-11-02): native DMOJ pages/Ace/polling and completed
identity/import/contest/session/scoring guards are the minimum product foundation.
Retain all historical acceptance. Finish only essential navigation, source-file
loading if absent, account-safe saved code and demonstrated usability gaps;
rejudge/history/finalization/export require bounded native-tools acceptance.
New combined browser acceptance is pending, not established by old runs. Defer
Monaco/split/new draft sync/custom Run/extra languages/redesign and all other
[deferred tasks](MVP_DEPENDENCIES.md). Logo artwork is nonblocking. One server with
isolated worker is sufficient; internet allowed. Production/network/restore/
worker recovery/representative load are a separate checklist. No fixed 150+/300
capacity claim or public deployment. Current task changed documentation only.

Branch `polygon-dmoj-compat` (only listed local branch), HEAD `48db2e7`: newer successful work is uncommitted.
Preserve the existing dirty tree; pre-A02 filenames/hashes/status are saved in
`build/a02-converter-1/before-files.json` and `before-status.txt`.

## Working commands and observations

Historical 2026-10-30 documentation corrections (later C12 completion and current scope supersede pending/dependency wording): C18/C19 are contiguous separate Phase C
rows; C12 remains PARTIAL with passed C05/C07/C10 coverage retained and only the
unevidenced upload cases named above. G15 stages/deploys on the college server
**after G13 backup/restore and G04 readiness**, then G14 tests actual campus/guest
LAN access; H03/H05 retain both gates. No application/service changes, runtime
reruns, historical report edits, new audit bundle, commit or push. Validation:
`python3 -B -` (inline Markdown-table/dependency/link checks), exit0;114 task IDs,
19 contiguous Phase C rows, no missing IDs/cycles/deferred prerequisites;91 selected
tasks equal the H05 dependency closure. `git diff --check`, exit0.

2026-10-30 documentation consolidation checks: `python3 -B -` (inline read-only
parser of plan task/dependency columns and local Markdown links), exit **0**:
114 unique task IDs, no missing dependency IDs/cycles, all 91 selected tasks form
a closed graph without deferred prerequisites, 172 local links resolve.
`git diff --check`, exit **0**. Manual current-scope/history review complete;
no runtime, conversion or judging checks rerun. Only the plan, MVP_DEPENDENCIES,
this status and permissions/contest-rules contracts were edited; historical
reports were read only. No extra audit bundle or repository script created.


Current local website lifecycle (from repository root):

```sh
python3 -B deploy/site-local/manage.py start
python3 -B deploy/site-local/manage.py stop
python3 -B deploy/site-local/manage.py status
python3 -B deploy/site-local/manage.py accounts
```

Start/stop preserve the DB volume/accounts; credentials are not printed by accounts.
`up` is for a fresh installation and refuses collisions. `verify` preserves
passwords and performs no provisioning/migration application. `reset-accounts`
is an explicit operator action that reapplies the private development values.
Current behavior/focused commands: [follow-up](reports/b01-followup-1/README.md);
original baseline/failed attempts: [B01 report](reports/b01-site-1/README.md). B01 used no converter or
judge checks; historical commands/results below are preserved, not rerun.
Final saved-evidence audit: `python3 -B reports/b01-site-1/verify_evidence.py`
exited **0** (249-file preservation, private credential exclusion and unchanged
independent-review source/evidence hashes); no runtime checks repeated.

Use existing `.venv` (Python 3.14.4, PyYAML 6.0.3, defusedxml 0.7.1), `PCC_ROOT=/tmp/cp-judge-pcc` (clean pinned
checkout). Bootstrap's normal location is `.deps/converter`; no bootstrap/install
needed here. Every conversion output directory must be new.

```sh
PCC_ROOT=/tmp/cp-judge-pcc .venv/bin/python -B -m unittest discover -s tests -p test_conversion.py -v
PCC_ROOT=/tmp/cp-judge-pcc .venv/bin/python -B -m tools.pipeline --output build/a02-converter-1/pipeline --real local-packages/gaming-grid.zip
.venv/bin/python -B -m tools.verify_install local-packages/gaming-grid.zip build/a02-converter-1/pipeline/converted-3
```

A02: all **7 verification commands exited 0**: 6 existing regression tests passed,
4 package conversions and 4 preservation checks passed; **112 test pairs / 4 sample
pairs / 18 statement assets**, checker/header bytes, CPP17/CPP23, limits and scoring
metadata verified. Exported ZIPs match extracted bytes; synthetic hashes match prior
fixtures. The seventh command is a supplemental read-only metadata audit. Exact
commands/exits: [commands.json](reports/a02-converter-1/commands.json). No fixes or
new installations were needed. **Judging NOT TESTED by A02**; no Docker/native code
execution. Private outputs: `build/a02-converter-1/pipeline/`.

A03: **runner exit 0; independent review PASS**. All 18 probes / 454 ordered
verdict and score assertions passed: **452 executed cases + 2 expected SC/zero-point
dependency records**, never AC. Real reference 103 AC/103 asserted points; wrong
55 WA + 48 AC/48 points; runtime 103 RTE/0; timeout 103 TLE/0. Groups retain
30/50/20 point and dependency assertions; all synthetic probes pass. Six targeted
probe/result tests passed. A focused installer change fills previously missing
ungrouped `score_cases`; explicit group scores, runner, standards, pins and sandbox
are unchanged. Scores are verified by official DMOJ assertions, not printed numeric
case logs. [Exact commands/exits](reports/a03-judge-1/commands.json).

```sh
sg docker -c 'PCC_ROOT=/tmp/cp-judge-pcc .venv/bin/python -B -m tools.pipeline --output build/a03-judge-1/pipeline --real local-packages/gaming-grid.zip --judge --judge-image sha256:d8d9dded026cd9d2d4a4f41136b99fa935935f8638cab314ad0a0e567ebcf0e8'
```

Reused image above; full base/source/runtime identity in [A03 evidence](reports/a03-judge-1/evidence.json).
Docker 29.9.2, Python 3.14.7, GCC 16.2.0 and runtime locks were verified again;
live container restrictions were inspected. Private raw output: `build/a03-judge-1/`.
No A03 blockers, no executor/probe skips, no failed assertions. No commit/push.

Historical judging recipe: build
`Dockerfile.judge`, then use `tools.pipeline --judge` with a fresh output. That
session needed `sg docker -c '…'` to refresh Docker-group access; Docker client/server
29.9.2 and runtime Python 3.14.7/GCC 16.2.0 were recorded, not rechecked by A02.

## Decisions, retained A01 facts and limitations

- Reuse/pins: [dependencies.json](dependencies.json), [requirements.txt](requirements.txt),
  [requirements-judge.txt](requirements-judge.txt); PCC `41ce3afcedf6c02793b308ba2e6ddb2ea5f82134`,
  DMOJ `1245dc4158dbb9e906c4c103e1ea939e012ee79b`. Base/image digests are in
  [judge evidence](reports/judging-docker-resume.json). No pin changes for A02/A03.
- Limits: milliseconds / 1000 → seconds; ceil(raw bytes / 1024) → KiB. Raw bytes
  bypass PCC's intermediate MiB rounding (67108865 bytes → 65537 KiB). Real limits:
  2000 ms / 268435456 bytes → 2 s / 262144 KiB; checker/probes retain CPP23.
  Samples remain active cases plus sidecars. Corrected config is repacked into the
  exported ZIP. `install()` passes limits into test submissions; future website dispatch must do
  so too. YAML preservation alone does not establish enforcement or judging.
- Docker mounts/root remain read-only, network/socket absent, `/tmp` ephemeral,
  with resource caps and only SYS_PTRACE added after dropping capabilities.
- Real all-NO probe expectations are per test file: any jury YES implies WA,
  otherwise AC. Hence 55 WA / 48 AC, not 103 WA; empty feedback excludes PE.
  Numbered expectation/score mappings avoid DMOJ `ConfigNode` list handling;
  loading only supported C++ executors avoids unrelated Objective-C initialization.
  Exit zero with a skipped executor cannot count as PASS; every case must match.
- Historical TLE observations were 3.001–4.001 s for a configured 2 s busy loop.
  Exact timing parity and Polygon's MSYS2 GCC14 environment are not reproduced.
- One real export plus synthetic fixtures only. Multi-test all-or-nothing groups,
  jury internal errors, browser import/rendering/submission/standings, supported
  production website deployment, multi-worker recovery, offline operation and capacity remain untested.
  Group dependencies tested so far have one case per group; site aggregation is separate.
- Generators, validators and package scripts are not executed. Interactive/file-I/O
  packages, multiple testsets and partial checker-point protocols remain rejected.
  Preserved HTML/PDF assets are inert, not implemented safe web rendering.
- `THIRD_PARTY.md` retains a stale unpinned/untested-image paragraph; the current
  Dockerfile and later judge evidence supersede it. Older blocked reports remain
  historical. `conversion-report.json` and preservation tools correctly mark judging
  NOT TESTED within their own scope.
- Learning is handled in a separate ChatGPT conversation; no lessons/Q&A documents.
  Preserve unique user notes when consolidating; this status replaces prior orientation
  notes. No A02 blockers. No commit/push performed in that historical milestone.

A04 candidate: official site `6aaddea6aaeabf4927b83787714509ff9fff8897` (GNU AGPL v3),
docs `bfae0464438a1bb2570cde523837ed575c54197e`. Its Django >=4.2,<5 constraint
requires an A09 maintenance decision: 4.2 is EOL and excludes host Python 3.14.
No website setup/judge connection was tested; no dependencies installed or judging repeated.

A05 (historical broader scope): 20 features mapped (5 available upstream, 10 need modification, 4 custom,
1 unknown). Native contests/groups/submissions/worker queue are reuse points, not
runtime guarantees. Important gaps: pre-start registration, late-entry controls,
true deregistration versus leaving active context, race-safe verified-email identity,
scoped private rosters, exact scoring/ties, Polygon publication and CPP23 bridged
checker installation, Monaco/autosave, team/match identity and custom Run extension.
Team/match and participant-group features in that map are now deferred. Native
batch dependencies exist; stock checker UI omits bridged. A03 does not prove
site/bridge/browser/standings compatibility. A05 source-reference checks passed;
no website dependencies, service startups, browser tests or judging reruns occurred.

Additional source gap: both stock site language fixtures omit CPP23, despite A03
worker support; B03 verified the existing accurate GNU C++23 database mapping and
native handshake without changing it. B04/B05 now map the private installed
problem's allowed language exactly to CPP23, without LanguageLimit overrides.

A09 selected official **unmerged** `django-52-upgrade` commit
`604d60cfd764bc708b04ffd75b715a5398b91f8b` (AGPL v3), with no local application
patches. Tested **Python 3.12.16 / Django 5.2.18 / MariaDB 11.4.13 / Celery 5.6.3 /
Redis 7.4.12 / Node 22.23.4** in separate pinned images. Full Python/npm locks,
native versions, source provenance and logs: [A09](reports/a09-site-1/README.md).
Locked website image: `sha256:3ea8c0fbeb13e683ad0ba580b612c1c8987260f1617a6aafeca8aec751d9d99a`.

```sh
sg docker -c 'docker build --progress=plain -t cpjudge-a09-site:locked build/a09-site-1/context'
sg docker -c 'python3 -B reports/a09-site-1/verify.py --work-dir build/a09-site-1/replay --prefix cpjudge-a09-replay1 --image cpjudge-a09-site:locked'
```

Both exited **0**. For another run use the report's fresh-directory recipe; the
saved replay directory must not be reused. Installation/pip check, 201 migrations,
79 upstream tests, login/CSRF/session, 15 static HTTP probes, Redis/Celery task and
disposable DB backup/restore passed. All A09 containers/networks were removed.
`CPP23` native Language metadata was created/verified; no worker/runtime records
were fabricated and C++23 standards remain unchanged. Converter venv, judge image,
application files, dependency pins and previous evidence were preserved.

Historical A09 limitations: `makemigrations --check --dry-run` **failed exit 1**, with 11
metadata-only changes and no generated DDL; retained as a failed supplemental
diagnostic. MariaDB cannot create Class's conditional name constraint (existing
unconditional uniqueness verified); upstream warnings and four deployment warnings
remain. Development HTTP startup is tested, not production hardening, browser JS,
OAuth/2FA, events or site/bridge/worker submission compatibility. Phase B must
verify real CPP23 enrollment, checker installation, verdicts/scores and standings.

B01 resolution: A09 evidence remains unchanged; current migration consistency
passes with the bounded forward fix in `patches/site/` and
`deploy/site-local/migrations/0153_reconcile_model_metadata.py`. Default timezone,
checker/runtime standards and native auth are retained. The bounded follow-up adds tested native profile/synthetic statement/preview
math, admin shortcut transport and password preservation/reset behavior. It does
not certify actual imported statements, judging, standings or all admin features at that historical B01 boundary.
