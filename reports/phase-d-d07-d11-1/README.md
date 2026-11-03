# D07–D09 and D11 — local PASS

Completed sequentially by one agent; stop before D13. D10/D12/D14/D15 remain deferred.
Native DMOJ participations, fixed scorer, templates and Phase C immutable-version/
probe/worker checks are retained. Additive migration0011 adds registration state
and durable submission receipts. No new account, password operation, import,
conversion, sandbox/limit change, commit or push.

Registration and withdrawal are idempotent. Published eligible provisioned users
may register before start or late until the common end; withdrawal closes exactly
at start. Native leave clears navigation only. Authors/content reviewers cannot
register officially in their own scope; later grants retain conflict history and
unrank the native entry. Basic scoped roster shows names/handles, private email
and state; participants/unrelated authors cannot fetch it. Managed CSV stays disabled.

Removal/DQ require a reason and audit. Removal preserves score/rank with a Removed
marker; DQ preserves evidence/earned score but excludes the entry from ranks and
shows DQ. Both revoke scoped reads, assets, submissions, polling and rejoin.
Other contests retain their permissions. Registration/admission share the contest
lock and sample server time after it. Removal locks both accounts in ID order
before the contest (including audit foreign keys), then rechecks session/scope.
Explicit contest submission forms record receipt, immutable version/runtime and
idempotency key atomically; retries return the original submission, including
after end. Native direct POST cannot become practice or choose another contest.
Already admitted jobs remain valid after removal/end/session changes.

| Actual checks | Result |
| --- | --- |
| Focused MariaDB/HTTP tests | **10 PASS, 0 skips:** duplicate registration/withdrawal and submission races; register/withdraw/submit clocks sampled after a contended lock; exact start/end; removal versus admission; stale sessions; author conflicts; CSRF/methods; scope/roster/email/privacy; native leave/direct submission/poll denial; removal retains score and DQ promotes the remaining entry. Constructed verdicts here are not actual judging. |
| Relevant regressions | **12 PASS, 0 skips:** six existing email-only session/password checks, four author draft/version/schedule/fixed-preset checks, and two D01 privacy/boundary tests updated for active registration and durable receipts. Synthetic test-DB resets do not change live passwords. |
| Actual Chromium | Pre-start register → deregister → register; idempotent retry and native leave; late entry after the actual UTC start, shared deadline, no late withdrawal; private roster/denied unrelated management; reasoned removal → DQ; native/direct read, asset, submit, source/case polling and rejoin denials. Other existing problem remains accessible. [Browser](browser.json). |
| Actual native judging/standings | Exactly **submission23: CPP17 AC on all3 cases**,0.5s/65536KiB problem limits, one durable receipt and exact retry. SQL independently verifies complete cases, native worker, retained solved point after DQ, reason audits, late entrant common start/end and sole remaining **rank1**. [Preservation/results](preservation.json). |
| Preservation/operations | Full private backup before migration, gzip readback; **70 prior model sets /2138 non-session rows checked**. Original passwords/accounts/imports/source/cases/contests/audits preserved; expected login/liveness and the selected problem's native AC-rate/user-count aggregates differ. Prior navigation pointers restored; runtime advertisement content and sandbox retained. Schema consistency/AST/whitespace pass. [Checks](checks.json), [exact commands/exits](commands.json). Backup restore was not rerun. |

Private credentials/source/screenshots/raw logs and backup remain ignored under
`build/phase-d-d07-d11-1/`. Failed attempts are retained: the real race exposed and
fixed an audit-FK deadlock; legacy blank-email test fixtures and browser editor/
newline assertions were corrected. Browser resumes never duplicate admitted work.
The first task-owned fixture expired naturally. Its entry was removed with a
reason/audit to isolate access to the reused version; the second fixture's completed
pre-start browser actions were cross-checked against their exact pre-start audits
before resuming. Neither schedule was extended or reset. One version may still
be legitimately accessible through another authorized contest; removal is scoped.

Manual test: sign in as an author at **http://127.0.0.1:8000/author/contests/**,
create/publish a future contest using the existing workflow. Open `/contest/KEY`
as a provisioned participant and use Register/Deregister before start. Re-enter
while running or register late: the end stays fixed and Deregister is unavailable.
As the owning author/scoped admin, open **Roster and entrant management**, enter a
reason, then Remove or Disqualify. Refresh standings and retry the participant's
old problem/submit/poll URLs. Local accepted fixture: `/contest/d07local2`;
author roster: `/contest/d07local2/roster`.

Limits: local proof, not capacity/crash recovery, configurable registration windows/
capacity, restoration UI, D13 author testing, rejudge/finalization or full E workspace
acceptance. Historical contests/entries keep their legacy policy. No deferred UI work.
