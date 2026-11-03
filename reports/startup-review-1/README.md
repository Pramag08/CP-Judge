# Local startup and judging review — 2026-11-02

**PASS for the checked local service path.** A fresh labelled browser submission36 was actually judged AC on 103/103 cases before the temporary contest ended. A supported idle stop/start then preserved its verdict and browser access; the native CPP23 worker reconnected and advertised the exact private version. No account, password, database volume, imported problem, worker key, or sandbox setting was reset or replaced.

The review found two health-reporting gaps. `b02.py start` previously accepted a process launch without bounded process readiness, and `b02.py status` returned zero when bridge or Celery counts were zero. `manage.py status` also did not require a running worker or native online/executor state. Now B02 start polls both processes for up to 20 seconds and gives sanitized counts on failure; B02 status requires bridge/Celery and the event state appropriate to the active polling mode. Top-level status requires running DB, Redis and worker containers plus native online/executors. Top-level start runs that complete status gate before reporting success. The retired event container remains stopped as designed.

| Check (exact command unless described below) | Exit | Observed |
| --- | ---: | --- |
| `python3 -B deploy/site-local/b02.py status` | 0 | Bridge 1, Celery 1, retired event container false. |
| `python3 -B deploy/site-local/manage.py start` | 0 | B02/B03 start passed; after fix, `post-start-status` also exited 0 before URL was printed. |
| `python3 -B deploy/site-local/manage.py status` | 0 | Required containers/services, native worker and website checks passed. |
| Chromium `browser_check.py` from the prior repair, with fresh output `build/startup-review-1/` | 0 | Email/password login and labelled submission36 displayed AC through case103. |
| Read-only Django ORM assertions for submission36 and worker | 0 | Stored final AC, 103 AC cases at 1/1 point, CPP23, exact version `pv900000000000000003`; connected worker advertised it. |
| `sg docker -c 'docker exec cpjudge-b01-site python manage.py check'` | 0 | No system-check issues; upstream initialization warning and 51 silenced checks remain. |
| `python3 -B deploy/site-local/manage.py stop` | 0 | Idle worker stopped first; site, Redis and DB stopped; named DB volume retained. |
| `python3 -B deploy/site-local/manage.py start` after stop | 0 | Same containers restarted; B02 and B03 passed. |
| `python3 -B deploy/site-local/manage.py status` after restart | 0 | All required live checks passed. |
| Chromium `post_restart_login.py` with fresh output under `build/startup-review-1/` | 0 | Email login and prior submission36 page accessible after restart. |
| Read-only ORM assertions after restart | 0 | Submission36 still AC on 103 cases; worker online with exact version and CPP23. |
| Private worker readiness socket connection on 127.0.0.1:9994 | 0 | Accepted connection after restart. |
| `python3 -B -m py_compile deploy/site-local/manage.py deploy/site-local/b02.py deploy/site-local/b03.py` | 0 | Changed lifecycle sources compile. |
| `git diff --check` | 0 | No whitespace errors. |

The exact browser invocations used the pinned `cpjudge-b01-browser:local1` image with `--user 1000:1000 --network host --shm-size 256m --cap-drop ALL --security-opt no-new-privileges`; they mounted the existing ignored `build/import-capacity-1/` fixture read-only at `/run`, mounted `build/startup-review-1/` at `/results`, and mounted each ignored browser script read-only at `/tests/`. The first script was `build/startup-status-fix-1/browser_check.py`; the second was `build/startup-review-1/post_restart_login.py`. The read-only ORM probes asserted the nonsecret fields listed above and printed only pass summaries. Docker inspection showed `cpjudge-b01-data:/var/lib/mysql`, the pinned worker image, read-only worker root and container-network mode. Raw fixture and browser outputs remain ignored under `build/`.

Untested here: forced service-failure branches, an in-progress judge crash, production/campus operation and every unrelated project feature. The temporary contest ended after submission36, so no new post-restart submission was attempted. The restart did confirm persistence and worker readiness. Next task: previously selected MVP work only on request.
