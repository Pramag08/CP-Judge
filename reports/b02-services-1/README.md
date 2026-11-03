# B02 — native local services

**PASS for B02 readiness.** [Result](result.json), [independent review](review.json),
[preservation](preservation.json), [native process log summary](native-log-summary.json).

B02 adds the selected site's real `runbridged`, Celery worker and websocket event
daemon to the existing B01 deployment. No worker enrollment or successful judging
is established. Source remains DMOJ site 604d60cfd764bc708b04ffd75b715a5398b91f8b;
AGPL attribution and the B01 migration/template/math overlays are preserved.

Configuration/code: deploy/site-local/b02_config.py, b02.py, b02_process.py,
b02_probe.py; native websocket/daemon.js plus the small reviewed
patches/site/0004-event-set-iteration.patch. Event npm versions and integrity are
locked in deploy/site-local/events/package-lock.json; Node uses A09's pinned
image. Python reuses the running locked website image/environment; no reinstall.

## Services and commands

- MariaDB/Redis/website retain their original containers and database volume.
- Bridge: native manage.py runbridged inside site; judge and Django interfaces
  bind container loopback 9999/9998. No judge credentials or worker records added.
- Celery: native dmoj_celery application, solo worker/concurrency1, b02@site;
  existing Redis databases 1/2 are broker/results, database0 remains site cache.
  No Celery beat is needed/configured for this bounded gate.
- Event daemon: pinned site's real Node daemon, private Docker sender port9997;
  only consumer WS9996/HTTP9995 are published to host127.0.0.1. The site's real
  event_poster posts to events:9997. Native daemon has no auth command, so key=None
  is explicit and private sender isolation is required; no fake auth was added.

```sh
python3 -B deploy/site-local/manage.py start
python3 -B deploy/site-local/manage.py stop
python3 -B deploy/site-local/manage.py status
python3 -B deploy/site-local/b02.py verify
```

Existing lifecycle now starts/stops B02 roles in dependency order. A serialized
process controller detects exact owned bridge/worker command lines and refuses
duplicates. Native bridge startup resets judge flags and in-progress submissions;
B02 therefore refuses startup when judges or in-progress jobs exist. Revisit that
policy explicitly in B03 rather than resetting future real work. Ordinary website
verification remains non-mutating and never calls account-reset/provisioning.

For first setup on a fresh established B01 deployment:
`python3 -B deploy/site-local/b02.py setup`. It generates no credentials, uses
existing private site settings, installs the exact event lock, appends only the
B02 configuration, and reloads only the web process. Source/initial configuration
checks must precede use on a different source pin. This run's fresh commands/exits
and logs are in commands.json; raw private browser/process details stay in build/.

## Executed checks and limits

The result-*.json files record actual native Celery ping and demo.success broker/
worker/result completion; exact diagnostic payload+ID delivery through the site's
real poster to a WS receiver and the daemon's HTTP poll endpoint; a supported
bridge terminate-submission request for missing ID -1 returning aborted:false;
and TCP availability of the judge listener, with no handshake/enrollment.
Browser-*.json records real Chromium website styling/login/logout, invalid login
and participant-admin denial. Password hashes are compared to the private initial
snapshot before and after; no password reseeding is used. Restart repeats task/
event/bridge/browser checks; repeated start must retain one process per role.

Failures retained: initial nonexistent qu0.0.0 (registry query established actual
qu0.1.0); setup-helper string syntax corrected before retry; native daemon's
Set.each call incompatible with simplesets1.0.0. The minimal patch uses the real
array().forEach API for follower/poller iteration, including removal-safe snapshots.
The crashed event log and failed probe remain evidence, not passes.

Events and Redis broker/results are development volatile state, not durable event
replay. Reconnect/readiness tests do not prove replay or official-job recovery.
Native HTTP polling has no cross-origin CORS headers: internal HTTP delivery is
verified, browser polling fallback is NOT certified. Host WS delivery is reachable;
full participant live-update/permissions behavior is later work. Production/system
warnings remain unchanged; no warning was silenced. B03 must establish an approved
worker route and real enrollment/compatibility. UI, import, judging and standings
remain untested. Initial npm audit reported ws advisories (audit exit1 retained). The same-major
fixed ws8.22.0 pin was installed explicitly, followed by a fresh audit and real
event/task/bridge/browser checks; no forced automatic upgrade or warning suppression.
No commit/push.
