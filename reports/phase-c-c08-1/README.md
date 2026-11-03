# C08 — private compatibility preview

**COMPLETE — local PASS, one agent.** The existing owner-only `/imports/<id>/`
page shows problem/package identity, counts, explicit limits, C++ testlib checker
standard, converted scoring groups/dependencies, supported features and warnings.
It reads C07's persisted output without reconversion. Current owner/attempt
manifest, token-specific output reference, package digest, counts, limits and
checker standard must agree; missing details stay unavailable. Original group
names and reference/submission compiler requirements were not recorded and remain
explicitly unverified. Group numbers are converted configuration positions.

The native template escapes package text and uses private/no-store responses.
Raw HTML, hidden tests, source, internal paths and logs are excluded. Fixed
rejection guidance explains corrections for unsupported archive/compiler/scoring
features; unknown errors are suppressed. No standard/scoring downgrade.
**Converted successfully** is separate from **Judging verified: No — NOT TESTED**
and **Not ready for publication**.

| Check | Observed result |
| --- | --- |
| Actual successful conversion + refresh | Persisted C07 job13 and new actual Celery jobs17/21 display matching findings after refresh. Job17 used a malicious problem name; job21 is the supported groups fixture and observed queued→running→succeeded. |
| Unsupported package | New actual conversion18 failed for interactive metadata, with specific batch-version/platform guidance. No successful findings displayed. |
| Pending/failed and stale attempts | Real queued/running/failed pages show no successful preview. Constructed live fixtures14–16 deliberately contained findings from13 and hostile error text: stale findings and raw error text were suppressed. Native tests also verify retry clears findings, wrong manifests/digests/counts/limits fail closed and missing metadata stays unavailable. |
| Authorization and escaping | Actual Chromium participant/unrelated-author requests denied; native tests also deny revoked owner. Malicious name renders literally with no injected DOM/execution after refresh; hostile error text is replaced, not rendered. |
| Output agreement | Actual browser counts/limits/standards/fingerprints equal stored conversion-report/init output for13/17/21. All have3 tests/1 sample,500ms→0.5seconds,67108864bytes→65536KiB, CPP17. Group21 shows30/50/20points; group2 depends on1. Unit receipt additionally checks67108865bytes→65537KiB and CPP23. |
| Focused tests | Final28 passed, exit0:7 C08 +10 C07 +8 existing upload +3 extraction regressions. Earlier25-test runs overlap; they are not additional unique checks. |
| Preservation |63 model sets/1756 preexisting rows preserved, allowing only login/access/session-generation and judge liveness changes. Passwords, college IDs, submissions/results and keys unchanged. All four container IDs/images/configuration/start times unchanged. No migrations or configuration changes; only HTTP/Celery processes reloaded. |

Evidence: [browser](browser.json), [stored-output agreement](output-agreement.json),
[rows](preservation.json), [containers](containers-preserved.json),
[exact subprocess commands/exits](commands.json). Private command logs, original
snapshot and browser fixtures remain under ignored `build/phase-c-c08-1/`.
Earlier attempts are in the ledger: the first browser exploration stopped before
upload because Playwright refused an oversized buffer. The111MiB private real ZIP
also exceeds the existing32MiB upload limit; limits were preserved. Acceptance
uses actual conversions of supported synthetic Polygon exports, not a new import
of that large private archive. Initial sandbox `sg` denials were rerun with Docker
approval. No failed exploration is counted as passing.

Final commands from repository root (all exit0):

```sh
sg docker -c 'python3 -B deploy/phase-c/c08.py stage'
sg docker -c 'python3 -B deploy/phase-c/c08.py tests'
sg docker -c 'python3 -B deploy/phase-c/c08.py activate'
sg docker -c 'python3 -B deploy/phase-c/c08.py browser'
sg docker -c 'python3 -B deploy/phase-c/c08.py verify-output'
sg docker -c 'python3 -B deploy/phase-c/c08.py preserve'
git diff --check
```

`stage`/`activate` change code/processes; ordinary checking should reuse saved
evidence. One-time `snapshot`/`fixtures` actions already ran; preserve their
baseline. Browser reruns review completed jobs, renew only C08 constructed fixture
leases and use fresh private output directories. Fixtures14–16 were never queued
to Celery and expire through C07 reconciliation. Historical reports are unchanged.

No C08 blocker. Judging, original group names/reference compiler verification,
statement/asset preview, publication and worker readiness remain **NOT TESTED** by
C08. Next: **C09 only on request**. No probes, redesign, commit or push.
