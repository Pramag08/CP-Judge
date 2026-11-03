# C09 — private statement preview

**COMPLETE — local preview PASS, one agent; full real-archive import limitation below.**
Owner plus current scoped import capability is required for `/imports/<id>/statement/`
and every attempt-bound asset URL. C08's successful output/owner manifest checks,
C05 source digest/private storage and existing presentation sanitizer are reused.
The DMOJ template uses B06's structural classes, sample-line normalization and
existing local MathJax3.2.2 loader. Preview is explicitly separate from publication.

Only declared UTF-8 HTML under `statements/` and its referenced local images are
read from the digest-verified ZIP; no extraction or general file-serving route.
An explicit tag/class/TeX allowlist removes active markup, links, events and all
uploaded CSS/resource loading. Removal notices require author review; missing,
unsafe or unsupported content suppresses the entire statement. First declared
HTML language only; alternatives are reported. PDF/SVG and alternative math
syntax are unsupported. Image bytes must decode as single-frame PNG/JPEG/WebP;
re-encoding strips metadata/polyglot payloads and serves only PNG. Filename/MIME
claims never select the served type. Limits:4MiB HTML,8MiB/image,16M pixels/image,
32 images,24MiB original/rendered image totals. Mixed sample markup that would
lose text is rejected. Private/no-store, nosniff and no-referrer protect previews;
assets additionally use an inert CSP. Hidden tests, answers, source and raw ZIPs
cannot be fetched through these routes. C05's separate existing owner download
is unchanged. No migration, publication, worker change or judging probe.

| Actual check | Result |
| --- | --- |
| Final focused suite |39 tests,0 skips, exit0:10 new C09 +7 inherited C08 +4 sanitizer +10 C07 +8 upload checks. Includes revocation, XML entities, declared/source traversal, image bombs/polyglots, current receipts, sample integrity and type spoofing. |
| Chromium final conversions31–35 | Exact unchanged real statement HTML in a supported synthetic Polygon conversion:30 ordered equations, sections and both samples match the original; screenshot inspected. Separate supported image fixture decodes, loads and returns PNG/private/nosniff. |
| Malicious fixtures | Scripts/events/iframe/SVG/object/links and CSS URLs absent from the returned statement HTML **before rendering**. Playwright requests and Chromium Network.requestWillBeSent both observe **zero fixture external attempts**; no injected state or page errors. Routing would count an attempted blocked request as failure. Existing native Gravatar decoration still attempts its external host and is blocked by the test harness; no site-wide offline claim. |
| Direct access | Actual logged-out, participant and unrelated-author preview/asset requests denied. Native tests additionally revoke the owner. Traversal, hidden/source/raw names, fake image suffixes, wrong attempts and cross-import asset URLs rejected. SVG bytes named `.png`, external image URLs and unsafe TeX show no partial statement. |
| Refresh/retry | Actual job24 was deliberately marked failed with stale findings retained; page/old asset denied. Native UI retry ran through Celery to successful attempt2; refresh/image use attempt2, attempt1 asset remains404. Constructed queued/running/failed jobs28–30 also suppress stale preview/assets after refresh; these are not extra conversion successes. |
| Preservation |63 model sets/1762 prior rows preserved, permitting native login/access/session-generation and judge-liveness changes only. Passwords/IDs/results/keys unchanged; all four container IDs/images/configuration/start times unchanged. Only HTTP reloaded; Celery/bridge/worker retained. |

[Browser results](browser.json), [retry/state results](states.json),
[focused checks/pins/source hashes](checks.json), [rows](preservation.json),
[containers](containers-preserved.json), [exact subprocess commands/exits](commands.json).
Raw logs, screenshots, original snapshot and private fixture bytes remain ignored
under `build/phase-c-c09-1/`; earlier runs are retained.

**Limitation:** the only real original ZIP is111MiB/247507278 expanded bytes,
above unchanged32MiB upload/128MiB conversion limits. Full original-archive
C09 upload/conversion acceptance is **NOT TESTED**. Its unchanged statement HTML
was placed in the existing supported synthetic test/checker package, then uploaded
and genuinely converted; this proves real statement rendering, not acceptance or
judging of that original problem. It has no referenced images; approved images
are verified separately. Load/concurrent-revocation races and browser-engine
coverage beyond Chromium are untested. Preview revalidates and sanitizes on each
request; it is not a production throughput benchmark.

Final commands from repository root (each final execution exit0):

```sh
sg docker -c 'python3 -B deploy/phase-c/c09.py snapshot'
sg docker -c 'python3 -B deploy/phase-c/c09.py stage'
sg docker -c 'python3 -B deploy/phase-c/c09.py tests'
sg docker -c 'python3 -B deploy/phase-c/c09.py activate'
sg docker -c 'python3 -B deploy/phase-c/c09.py browser'
sg docker -c 'python3 -B deploy/phase-c/c09.py state-checks'
sg docker -c 'python3 -B deploy/phase-c/c09.py preserve'
git diff --check
```

`snapshot` and `state-checks` are one-time fixture actions, guarded against replay;
reuse saved evidence. Browser reruns create fresh private output and may add imports.
Failed harness attempts are retained: missing browser lxml (removed dependency),
equation counting included head configuration (corrected to body), a missing local
MathJax include (fixed), and39-test login-counter interference (test-local cache
isolation fixed). An initial driver quoting syntax error and sandbox `sg` denials
also exited1 before mutations and were corrected/retried with Docker approval.
None counts as a pass. Final39 tests and final Chromium run cover final code.
**Next: C10 only on request.** No judging probes, redesign, commit or push.
