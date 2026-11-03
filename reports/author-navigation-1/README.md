# Author navigation follow-up — 2026-11-03

**PASS for the requested local browser path.** `b01-staff` (user 1) is active, staff, superuser and explicitly `Identity.is_author=True`; its pre-existing active `problems.publish` grant on `icap111a` permits selection of the original published version. Staff/superuser status alone does not grant author routing: `contest_manage.author()` requires the identity flag, and problem selection queries active `problems.publish` scopes. Participant author routes remain denied.

The original unchanged Polygon import is job 58, owned by `C1LIVEA` in source contest `icap111a`. Its immutable version 3, `pv900000000000000003` (“Pramag's Gaming Grid”), is `published` and its native problem is private (`is_public=False`). The job detail remains owner-scoped. This task did not upload, convert, publish, probe or judge the package.

The existing base template already held Create contest and Manage contests / imports links in its hover menu. The top-right trigger gave no role cue. It now visibly says **Author ▾** for authorized authors and opens their contest list on click; the existing menu retains the two actions. The navigation processor is registered with Jinja in settings before engine initialization, rather than appended during app startup. The participant trigger and menu do not expose author actions. Import remains scoped through a contest's management page.

Chromium used the existing local browser image and ignored private fixture. The first pass created private draft `navproof26` under `b01-staff` and selected existing version 3 as problem A/order 0; its later assertion failed because the author list displays title rather than key. The corrected final pass reused that draft and exited 0, checking visible Author trigger and links, create form GET, selected version in the draft, author listing, scoped import page, participant menu absence and direct 403/404 denials. The new draft is unpublished and retained. Final database inspection: version 3 still published/private; draft owner `b01-staff`, selected code `pv900000000000000003`; 31 import jobs, 3 versions, 36 submissions. No existing accounts, passwords, imports, versions, contests, results or limits were reset or changed.

Commands and exits (repository root):

- `python3 -B deploy/site-local/manage.py status` — exit 0, site/DB/Redis/worker running.
- Read-only `docker exec cpjudge-b01-site python manage.py shell -c ...` queries via `sg docker -c` — exit 0 for final ownership/scope/row inspection. Four queued/running C08/C09 import rows were historical test fixtures; no active submission or actual import job was present before HTTP/Celery reload.
- `docker cp` of `deploy/phase-c/native_settings.py`, `deploy/phase-c/cpjudge/native.py` and `deploy/phase-c/cpjudge/templates/base.html` into their existing `/app/` paths — each exit 0.
- `python3 -B deploy/phase-c/c13_bundle.py reload` — exit 0 after each staged change; HTTP/Celery only, bridge/worker/data retained.
- `sg docker -c 'docker run --rm --network host -v /home/pramag/Documents/CP-Judge/build/author-nav-1:/results cpjudge-b01-browser:local1 python /results/browser.py'` — final exit 0; private result at `build/author-nav-1/result.json`.
- `sg docker -c 'docker exec cpjudge-b01-site python manage.py check'` — exit 0, no issues (51 silenced). `git diff --check` — exit 0.

Working local URLs: `http://127.0.0.1:8000/contests/` (eligible listing), `/author/contests/create/` (Create contest), `/author/contests/` (Manage contests / imports), `/author/contests/navproof26/` (private draft and selected version), `/contest/navproof26/import/` (scoped ZIP management). The original owner-only job detail is `/imports/58/`; the problem version is `pv900000000000000003` and is not a public archive item.

Limits: This is a navigation and reuse proof, not the pending full H03 combined import-to-judging journey, publication of the new draft, or production deployment. Next task remains only user-requested MVP work; H03 stays pending. No commit or push.
