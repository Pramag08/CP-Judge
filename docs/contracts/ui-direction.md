# Approved UI direction — DMOJ template adaptation

Approved 29 October 2026; **direction recorded, product UI not implemented by
this B01 follow-up**. Retain the existing DMOJ visual shell and adapt its server-
rendered templates and locally served assets. No separate frontend application
or replacement design system. This supersedes older Kattis-like visual references;
the permission, contest and scoring contracts remain authoritative.

| Existing shell | Approved use |
| --- | --- |
| Horizontal navigation/header | Keep structure and proportions; expose only authorized MVP navigation/actions |
| Centered main content | Keep existing content width/alignment and page composition |
| Compact tables | Reuse for eligible contests, problems, submissions and standings |
| Sidebar styling | Keep the existing visual treatment where a sidebar is useful; author controls stay scoped |
| Footer | Retain styling and upstream attribution |
| Existing template hierarchy | Adapt base/content/contest/problem/account templates; integrate the editor as a local component |

The signed-in homepage remains the **eligible contest list**, with contest name,
status, schedule/duration, participant count and the appropriate Register/Enter/
View Results action. Create Contest appears only with an author grant. This is a
product requirement, not a claim that the stock B01 homepage implements it.

Keep one ordinary individual contest path at every supported participant count.
Contest primary tabs remain Problems, My Submissions and Standings. D14
clarifications are deferred. Authors manage assigned contests, Polygon imports
and entrants through scoped controls. Account
administration and submitted-source/hidden-data access follow the separate
permissions contract. No teams, groups, matchmaking, ratings, format selectors,
general announcement navigation or client-selected authorization roles.

The current user-approved header uses the supplied **foobar** logo in the
existing top-left logo slot, with **foobar** browser titles and favicon. The profile menu stays at right. The designated
administrator retains both author management and ordinary participant-page
navigation without a role-mode switch. Keep source/license attribution in the
footer. This supersedes the earlier plain-text Contests-CPJudge header direction.

The problem workspace/editor can evolve inside the existing templates, retaining
shared navigation, centered content, theme styling and footer. No full-site SPA
is introduced. Existing account authentication and server permissions remain the
authority; visual role/navigation changes never grant access.

B01 follow-up work is limited to real admin dependency loading, locally bundled
math rendering, explicit static namespaces and verification/account-reset
separation. It does not implement the eligible homepage, problem import, judge
connection, scoring/standings or the planned UI feature tasks.

Current supervised, in-person MVP scope: D14 problem clarifications are deferred.
No standalone archive/problemset, practice, editorials, virtual participation or
announcements in navigation. Preserve native template shell and attribution.

## Minimum native scope — 2 November 2026

Current task is documentation only; no new runtime acceptance. Reuse native Ace,
separate statement/submit pages, submissions/cases/standings and authenticated
polling. Finish only eligible-home/authorized role links and Problems / My
Submissions / Standings navigation; hide unnecessary links without deleting
upstream backends. Preserve readable styling; CSS changes require a demonstrated
usability blocker. Monaco, split layout, draft synchronization/new autosave,
custom Run, extra languages and redesign are deferred. Preserve existing useful
features, with account-safe native saved-code isolation. No signup/Google/mail/
forced-change flow. Internet independence is optional. Classification and pending
acceptance: [current dependencies](../../MVP_DEPENDENCIES.md).
