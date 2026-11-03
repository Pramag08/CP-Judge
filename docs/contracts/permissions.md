# A06 — identity, permissions and sessions

Status: **C01–C04/C16/C17 integrated local checkpoint PASS**;
[actual historical checks and limits](../../reports/phase-c-checkpoint1-1/README.md).
That checkpoint verified college-ID login, a temporary-password forced-change gate,
scoped privacy and one-active-session enforcement. Those results remain complete.
**Phase C retained local gates now PASS**, including C18 email-only cutover and
C13/C19/integrated acceptance. [Current closure, checks and local recovery](../../reports/phase-c-c18-cutover-1/README.md).
All existing password hashes/account IDs/history are retained. Four existing local
fixtures received explicitly user-authorized organizer-assigned development addresses;
audits state mailbox verification and real participant identity claims are false.
Email-only mode is active; ordinary username routes cannot bypass it. C19 voluntary
change/outside-app recovery and C17 generation/hash admission remain enforced.
Historical checkpoint evidence is unchanged; no email delivery was introduced.
Full lifecycle/import/rejudge acceptance remains separate; additional delegation
UI is deferred. This contract defines the updated individual MVP target.

Authorized account administrators provision personal email/password accounts for
college and external participants. No mandatory college ID, college email, Google
login or public signup. One account per canonical email must be enforced by a
database unique constraint, including concurrent provisioning and email correction.
Normalize by trimming outer whitespace, validating supported email syntax and
lowercasing the entire address under the chosen case-insensitive login policy.
Reject unsupported syntax explicitly and store a private display address separately
if needed. Do not strip Gmail dots or +suffixes, infer provider aliases or link
accounts automatically. Emails are private to their owner and appropriately
scoped organizers; account administration permits only necessary account access.

### Migration, conflict handling and rollback

- Privately inventory existing addresses and normalization collisions before
  adding/enforcing the key or switching login. Missing, invalid or conflicting
  emails block affected identity cutover; obtain organizer-verified corrections.
  Never invent missing emails, merge identities or discard an account to resolve
  uniqueness. Explicitly authorized development fixtures may receive organizer-assigned
  development addresses; record that basis with mailbox/real-identity claims false.
  This exception does not verify a real participant or mailbox. Do not claim migration complete with unresolved accounts.
- Preserve account primary keys, existing password hashes, legacy college IDs,
  submissions, grants and audit history. College IDs retain their historical
  trim/ASCII-uppercase uniqueness/correction behavior as stored legacy data;
  they are no longer a required credential for new accounts. No bulk password
  reset or rewrite is part of this migration.
- Take a readable private backup; stage mapping/validation, canonical-key
  population and database constraint separately from login cutover. Serialize
  provisioning/corrections so races cannot evade uniqueness; rehearse migration
  and rollback in isolation before live change. Restrict/record the cutover write
  window. Unresolved cases stay private with actionable organizer resolution.
- C19 removes the first-login/reset gate and associated blocking flags/redirects
  without changing passwords. Preserve historical forced-change audit events and
  back up the prior gate state. Verify old and newly provisioned/reset credentials
  against the new policy, with C17 session generation and privacy regressions.
- Define a reversible cutover: retain prior identity/gate mappings until accepted,
  restore the prior authentication path/schema compatibility if rollout fails,
  and fence/revoke affected sessions so stale credentials cannot bypass policy.
  Rollback must preserve intervening accounts, password resets, submissions and
  audits; never blindly restore a stale DB over new contest data or replay resets.
  Document handling of email-only accounts if reverting to legacy login.

## Permission matrix

All grants are server-side and scoped to a contest or immutable problem version.
An author grant permits creating contests. Creation records explicit owner grants
for settings, problem assignment/import/publication, clarifications, roster read/
export, entrant management, submission/source review and scoped delegation. Hidden
package access additionally requires ownership/import of that problem or a jury
grant. Generic author membership is insufficient. Creation confers no access to
other authors' contests.
Additional editor/reviewer grants and delegation UI are deferred for the MVP;
keep owning author/admin scopes and any already implemented grants/checks. If
enabled, the owner may delegate individual capabilities within that contest, but
cannot grant account administration, machine access or powers they do not hold.
The server records grantor, scope, capability, grantee and revocation.

| Resource/action | Participant | Assigned author/delegate | Account administrator/operator |
| --- | --- | --- | --- |
| Discover eligible contest, schedule and registration count | Own eligible contests; no private roster | Own scope, including drafts | Only with contest scope; platform operations audited |
| Register/enter/submit | Own active account and entry, within rules | Unranked testing in own contest | Same conflict rule when inspecting contest internals |
| Statements, samples, published assets | Registered entrants while running; eligible viewers after end; no unreleased statements before start | Scoped statement/editor access | Requires contest/problem scope |
| Contest settings, problem assignment/order (D14 clarifications deferred) | Read published rules | Owner or delegated edit capability; post-start changes constrained by A07 | Requires scoped edit capability |
| Basic roster names/handles, legacy IDs and private emails; optional export | Own account only; standings expose display name/handle, never emails | Explicit `roster.read` in assigned contest; CSV export deferred, requires `roster.export` if enabled | Account detail for administration; bulk contest roster requires roster scope |
| Remove/disqualify/restore entry | No | Explicit `entrants.manage`; reason and audit mandatory | Requires contest capability |
| Submission result/cases/compile diagnostics | Own submissions while contest access remains active | `submissions.review` in that contest | Requires review scope |
| Submitted source/raw download | Own source while authorized | Explicit `source.review` in contest; ordinary authorship alone is insufficient | Account administration alone grants none |
| Hidden tests, answers, checker/reference source, package archive | Never, including after end | Explicit problem-version `jury.read`/import ownership; not generic contest edit | Trusted judge operators only as needed; no account-admin default |
| Import/revise/publish/rejudge | No | Explicit import/problem/publish/rejudge capabilities; owned problem access also required | Operator capability and scoped audit |
| Create/reset/disable accounts; grant author | No | No | `accounts.manage`; minimum required account fields; no password/source/test disclosure |
| Grant/revoke administrator privileges | No | No | Platform owner only; audited, never self-escalation by an author |
| Judge credentials/configuration, raw private logs | No | No | Trusted infrastructure operator only; outside website roster/account permissions |
| Audit trail | Own relevant receipts | Scoped management events with private data redacted | Explicit audit scope; secrets/passwords never logged |

Each policy applies to HTML, direct URLs, JSON, raw files, search, CSV, caches,
polling and live channels. A role selector changes the view only. The real site
has no client-controlled “Preview role” authorization. Deny unspecified actions;
avoid exposing existence of inaccessible private objects. Assets and events must
recheck the current grant/entry, not just possession of an old URL/channel token.
Hidden input/expected output, raw checker feedback and hidden-program stdout
never enter participant result payloads. Executed-case verdict/time/memory and
sanitized compilation errors are allowed; missing or skipped cases never pass.
Other participants' source stays private after the contest too; public source
release is a separate future policy.

## Conflicts, removal and examples

Contest owners, editors, jury/source reviewers, problem importers and testers
are unranked for the entire contest. Before giving one of these grants to an
entrant, warn the granting author and atomically mark the entry unranked; retain
an immutable conflict flag even if the grant is later revoked. Prior knowledge
of any assigned hidden package/reference also requires an unranked entry.
Account administration by itself is not contest-content access. Do not trust a
participant-supplied official/test flag. Rank eligibility is server-assigned.

- Author of contest A can participate officially in B only without B conflicts.
  Changing A's URL/ID to B cannot read B's roster, source or unpublished problems.
- A delegate with `roster.read` in A can see A's emails but cannot export them,
  review source, read hidden tests or grant themselves any of those permissions.
- A participant sees their source and authorized case metrics; knowing another
  submission ID does not expose its source, compile log or private metadata.
- Removing an entrant blocks contest reads, Run, Submit and self-rejoin across
  all sessions/channels immediately. Attempts and source remain stored for
  authorized reviewers. Other contests and account login remain available.
  A07 defines the distinct ranking effects of removal and disqualification.
- An author using participant preview submits only unranked attempts; switching
  profile view or revoking the grant cannot turn those attempts official.

## Accounts and a single active session

Only authorized account administrators provision accounts and passwords.
**No forced password change on first login or after an organizer reset.**
Participants contact organizers outside the application for recovery. No automated
email delivery or reset-token service is required. The administrator verifies the
requester outside the app, sets a new password through Django secure password
hashing and revokes all existing sessions. Audit actor, target, time and outcome,
never passwords, password hashes or reset secrets. Never recover/display a stored
password. Rate-limit authentication and reset operations. C19 replaces the historical forced-change gate without erasing its verified
historical behavior.

Choose **one active authenticated session per account**. A successful new login
replaces the old session, including on another browser/device; multiple tabs in
the same browser session are allowed. No per-device account limit, fingerprint,
IP binding or permanent hardware binding is claimed.

Implementation contract: serialize successful login and password/reset/disable
operations on the account row; atomically advance an authentication generation
and bind the new session to it. Check generation on every authenticated request,
Run/Submit transaction and live-channel authorization; stale cached sessions must
not bypass it. Revoke/close stale channels and reject their next action. Concurrent
logins leave only the last committed generation valid. Logout revokes the current
generation; stale logout must not revoke the replacement session. Password change
rotates into a new sole session for the current user; admin reset/disable revokes
all. In-flight jobs already durably admitted remain valid; stale requests that
have not passed transactional admission fail. Cookies require production secure,
HTTP-only, same-site settings and login/rotation must avoid fixation.

Updated required acceptance: C18 canonical-email normalization (including distinct
Gmail dots/+suffixes), database provisioning/correction races, missing/conflicting
identity handling, preserved accounts/passwords/IDs/history, migration and rollback;
C19 successful first/reset login without forced change, verified organizer recovery,
secret-free audit and reset-driven revocation; C17 simultaneous login, stale
request/channel/logout, password change/reset/disable and recovery regressions.
Keep A/B cross-contest privacy, exports/events/assets, conflict grant and removal
races for retained features. The earlier documentation consolidation ran no runtime checks. Current C18/C19
results and cutover blockers are in the bundle linked above; checkpoint1 remains
historical evidence. Optional CSV/delegation still require scope checks if enabled.

## Native reuse and gaps

Inspected A09 site pin `604d60cfd764bc708b04ffd75b715a5398b91f8b`:
[contest access/edit](https://github.com/DMOJ/online-judge/blob/604d60cfd764bc708b04ffd75b715a5398b91f8b/judge/models/contest.py),
[problem access/edit](https://github.com/DMOJ/online-judge/blob/604d60cfd764bc708b04ffd75b715a5398b91f8b/judge/models/problem.py),
[submission access](https://github.com/DMOJ/online-judge/blob/604d60cfd764bc708b04ffd75b715a5398b91f8b/judge/models/submission.py),
[login/password views](https://github.com/DMOJ/online-judge/blob/604d60cfd764bc708b04ffd75b715a5398b91f8b/judge/views/user.py),
and `dmoj/settings.py` (cached-db sessions). Reuse these and Django authentication;
global edit/private-data permissions and native source visibility are broader
than this matrix. Add scoped checks instead of assuming `is_staff`, a menu label,
or stock public/solved-source settings suffice. Native login inspected in A06 did
not implement the generation policy. A09 tested ordinary login only; C17 later
implemented and verified it locally in checkpoint1. Reuse that implementation.
