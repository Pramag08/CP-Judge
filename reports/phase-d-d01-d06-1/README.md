# D01–D06 — scoped local PASS

Completed sequentially by one agent. Supervised, in-person competitions; D14
clarifications deferred and removed from required dependencies. Stop before D07.

Scoped authors can create/edit private drafts, select their authorized immutable
versions, set unique labels/order, preview persisted limits/rules and publish.
Native DMOJ Contest/ContestProblem, templates, fixed `cpjudge_icpc_v1` scoring and
Phase C publication/probe/readiness mechanisms are reused. Dedicated additive
metadata stores timezone/labels; no repurposed native fields or Lua label scripts.
Schedule wall times use validated IANA zones, stored as UTC; ambiguous/nonexistent
DST times and invalid intervals are rejected. Countdowns are advisory and based
on server time. Published settings are locked. A schedule edit invalidates draft
approvals until explicit problem re-selection; remove/reselect reconciles enabled
languages while preserving other contests' approvals.

One policy admits active provisioned accounts to published schedule/rules, subject
to removal. It does not create registrations or global problem grants. Management
requires scoped capabilities; account administration alone grants no content access.
Publication requires exact immutable/native data, complete accepted actual probe
binding, the fixed preset, enabled approved language and a **fresh authenticated
challenge through the connected native bridge to C11's worker byte/runtime check**.
No cached positive readiness receipt or new DMOJ wire field. Dispatch retains C11's
independent fresh check. Problem statements/assets remain private before start.
The existing horizontal shell is retained; navigation is limited to contests,
home redirects to the contest list, and archive/editorial routes are denied.

| Actual verification | Result |
| --- | --- |
| Focused native DB/HTTP checks | 8 tests PASS, 0 skips: author/participant/unrelated scope, crafted formats, CSRF/methods, label/order/limits, timezone and DST, invalid schedules, missing/stale probes and worker rejection, frozen publication, edit/remove/reselect, private direct/API/assets, exact start-inclusive/end-exclusive access and persisted execution receipts. Positive worker transport is mocked only in these constructed test fixtures. |
| Actual Chromium | Existing author creates/edits/selects/previews/publishes `d01local1`; live readiness passes. Ordinary participant/unrelated author management denied. Invalid schedule/crafted format/missing problems block. Draft and scheduled direct problem/API/asset reads denied; eligible scheduled overview allowed; join blocked. [Browser result](browser.json). Private screenshots retained under build/. |
| Actual readiness channel | Fresh worker byte/runtime challenge passes; stale timestamp, wrong authentication and missing problem fail closed without data/configuration changes. [Readiness result](readiness.json). |
| Persisted state/preservation | 68 prior model sets / 2098 non-session rows preserved, including all prior accounts/password hashes, submissions/cases/source, imports/versions/probes, audits and contests. Runtime advertisements are natively recreated at reconnect: exact semantic content compared, not transient row IDs. Only login/access/generation and judge liveness differ. Label Q/order2, Asia/Kolkata 10:00–12:00 stored UTC04:30–06:30, native0.5s/65536KiB, fixed rules and private version verified. [Preservation](preservation.json). |
| Operations | Fresh full private backup before additive migration0010; gzip readback passed, restore not rerun. Idle guarded service reloads; same worker/configuration. Migration consistency and whitespace pass. [Exact command/exit ledger](commands.json). |

No conversion or judging was rerun; reuse version2 and its existing actual accepted
probe (historical evidence: [Phase C integration](../phase-c-integrated-1/README.md)).
All old passwords and sandbox settings retained. Private backup/raw logs/credentials
and screenshots: ignored `build/phase-d-d01-d06-1/`. Initial failures are retained in
the ledger: migration output directory permission, template context integration,
two test-fixture assumptions and a missing readiness-handler import. They were
corrected; the valid browser publication was accepted only after the live gate passed.

Local author page: **http://127.0.0.1:8000/author/contests/**.
Sign in with an existing author account, choose **Create contest**, enter ID/title/
description/timezone/local start/end, then save. Import a Polygon ZIP through the
scoped link if needed; finish conversion/private publication and run an accepted
known-solution probe from that import. Select the version, label and order, preview,
then **Publish contest** when checks pass. Schedule edits require re-selection.
The preserved browser example is `/author/contests/d01local1/`.

Limitations/next: **D07 registration remains NOT STARTED** and managed join requests
are deliberately denied. No D08 race/load acceptance, D11 removal UI, D13 author
submission UI, D14 clarification, finalization, production/deployment/capacity or
wall-clock boundary browser race claim. Boundary checks here use constructed DB
receipts and controlled server times, not new judging. Native participant workspace
and complete eligible-home/profile navigation remain later E tasks. A successful
publication cannot guarantee a worker stays online; dispatch still fails closed.
No redesign, new account, password reset, limit change, commit or push.
