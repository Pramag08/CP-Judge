# A04 — website foundation inspection

**COMPLETE — source inspection only. Website setup, migrations, asset builds and
site/judge compatibility are NOT TESTED.** No dependencies/services were installed
or started, no application code was imported, and A03 judging was not repeated.

Candidate: official DMOJ `online-judge`, commit
[`6aaddea6aaeabf4927b83787714509ff9fff8897`](https://github.com/DMOJ/online-judge/tree/6aaddea6aaeabf4927b83787714509ff9fff8897),
observed master, committed 2026-06-05, checked out detached and clean under ignored
`build/a04-site-foundation-1/site/`. License: **GNU Affero General Public License,
version 3**, from its [LICENSE](https://github.com/DMOJ/online-judge/blob/6aaddea6aaeabf4927b83787714509ff9fff8897/LICENSE).
This is an inspection baseline, not an approved deployable dependency or a claim
of an additional later-version license grant. Existing converter/judge pins stay unchanged.

The official installation source was separately pinned at DMOJ/docs
[`bfae0464438a1bb2570cde523837ed575c54197e`](https://github.com/DMOJ/docs/tree/bfae0464438a1bb2570cde523837ed575c54197e).
The rendered documentation endpoint returned 403; the official Git source supplied
[installation.md](https://github.com/DMOJ/docs/blob/bfae0464438a1bb2570cde523837ed575c54197e/docs/site/installation.md).
Clone access initially failed inside the sandbox (exit 128, DNS); the approved
outside-sandbox retries succeeded (exit 0). No installation command from the guide ran.

## Declared foundation versus the current machine

Site paths below are relative to that exact candidate; each file URL/hash is in
[source-pin.json](source-pin.json). Full dependency declarations are in
[requirements.json](requirements.json); read-only local observations and command
exit statuses are in [environment.json](environment.json) and [commands.json](commands.json).

| Component | Source/documented requirement | Observed local state; implication |
| --- | --- | --- |
| Python/Django | `requirements.txt`: `Django>=4.2,<5`; `.github/workflows/build.yml` uses Python 3.11. No separate supported-Python range declared by the site. | Host/project Python **3.14.4**; Django absent from the existing converter venv. Python 3.11/3.12 not on PATH. Current host Python does not satisfy Django 4.2's official support matrix. |
| Database | CI and official setup use the MySQL family; documented MariaDB, `mysqlclient`, utf8mb4, timezone data and strict SQL mode. | MariaDB/MySQL clients/config tools and mysqlclient absent from inventoried PATH/venv. `dmoj/settings.py` defaults to SQLite, but that does not establish a supported DMOJ SQLite deployment: e.g. `judge/views/ranked_submission.py` contains MySQL-specific SQL. |
| Python packages | Django ecosystem apps, Celery, lxml/lupa/llist and other requirements; VCS dependencies are floating and several packages have old upper bounds. | Only converter packages are available in this venv. No full transitive lock was found. Native extensions and forks need a fresh compatibility/maintenance audit. |
| Assets/build | `make_style.sh`: Sass, PostCSS CLI, Autoprefixer; gettext compilation; `resources/libs` Git submodule. No project-wide Node version/lock. | Node **22.22.1**, npm **9.2.0**, make/GCC available; Sass/PostCSS/Autoprefixer/msgfmt absent from PATH. Asset gitlink pinned to `cba2efbf86e6e933704d8130fe256f2eab18621a`, not initialized/fetched. No asset build tested. |
| Background tasks | `dmoj/celery.py`; official setup selects Redis for Celery broker/results. | Celery/redis Python distributions and redis-server absent from inventory; no broker connectivity tested. Complete broker extras must be included in the eventual lock. |
| Judge transport | `judge/management/commands/runbridged.py`, `judge/bridge/{daemon,judge_list,judge_handler,django_handler}.py`: authenticated workers and native queue/dispatch. | Existing A03 image runs CLI tests, not an enrolled daemon. No bridge started or site connected. Celery does not replace this dispatch path. |
| Live updates | `judge/event_poster.py` selects disabled, WebSocket or AMQP transport. Optional `websocket/daemon.js` requires `qu`, `ws`, `simplesets`; Python WebSocket client is separately documented. | No event packages/server installed or live subscription tested. Choose/lock the intended transport; do not assume RabbitMQ is mandatory when the WebSocket path is chosen. |
| Serving | Documented nginx/uWSGI/supervisor; Django development server for local investigation only. | These executables are absent from inventoried PATH; no HTTP server, TLS or supervisor setup tested. |
| Native prerequisites | Development headers, MySQL client libraries, XML/XSLT/zlib and gettext are needed by the documented build. | `dpkg-query` exited **1**: queried packages were missing or marked uninstalled. Exact output is retained; absence on PATH/in this venv does not exclude other containers or machines. |

## Current support finding — checked 28 October 2026

The previously identified concern is confirmed. Django's official
[7 April 2026 announcement](https://www.djangoproject.com/weblog/2026/apr/07/security-releases/)
ends 4.2 extended support; its [4.2 Python matrix](https://docs.djangoproject.com/en/4.2/faq/install/)
includes 3.8–3.12, not 3.14. Installing on an accepted Python minor would not restore
framework maintenance. Conversely, Python 3.14 being a maintained branch does not
make Django 4.2 support it. No failed import/startup is claimed: none was attempted.

A possible modernization investigation is a supported **Django 5.2 LTS** stack:
[the support table](https://www.djangoproject.com/download/) lists security support
through April 2028, and the [5.2 matrix](https://docs.djangoproject.com/en/5.2/faq/install/)
adds Python 3.14 in 5.2.8. This is an **unvalidated A09 option**, not a selected
working stack. Root constraints such as `packaging<22`, `importlib-metadata<5`,
`mistune<2`, fixed social-auth versions and floating fork URLs need resolution;
changing only `Django<5` is not an upgrade validation.

The install guide's Node 18 and source CI's Node 20 are both now EOL according to
[Node's official lifecycle](https://nodejs.org/en/about/previous-releases). Host
Node 22 is on a supported LTS branch; asset/event compatibility is still untested.
[Python lifecycle](https://devguide.python.org/versions/) shows 3.14 maintained and
3.12 security-only; A09 must choose current supported micro releases rather than
blindly reproducing this host's patch. Select a maintained MariaDB/MySQL series
against the chosen framework's [database requirements](https://docs.djangoproject.com/en/5.2/ref/databases/)
and the vendor's [maintenance policy](https://mariadb.org/about/#maintenance-policy).
No database release is pinned or certified here.

## A09 gate and downstream compatibility checks

The unchanged candidate fails the plan's maintained-stack deployment gate. A04 is
complete because the source pin, requirements and risks are recorded; A09 remains
necessary, and website feature work must not treat this audit as startup evidence.

1. Establish a maintained official revision, reviewed maintained fork, or bounded
   upgrade from this baseline. Record exact source/patches and a support decision;
   do not silently switch platforms or treat a legacy reproduction as deployment approval.
2. Isolate the website environment from the converter and judge. Resolve and lock
   all transitive Python packages, VCS commit refs, native build libraries, frontend
   tools/event packages and asset gitlink; audit fork maintenance and removed APIs.
3. In a disposable authorized environment, verify actual installation, `manage.py check`,
   database migrations and `manage.py test judge` against a supported MySQL/MariaDB
   release. Exercise authentication/session/cache behavior, initial data and a migration
   rollback/restore path. Capture actual commands/exits and required patches.
4. Resolve asset submodules; run stylesheet/i18n/static collection checks with the
   supported pinned Node/tools. Render a stock page and confirm required assets load
   locally; avoid assuming current unversioned event dependencies preserve old APIs.
5. Test web/Celery/Redis startup and task execution, then record the required bridge
   and event-service topology. The optional gevent bridge entrypoint has extra
   dependencies; it is not the default `runbridged` path.
6. Inspect the selected site's wire/schema expectations against pinned judge
   `1245dc4158dbb9e906c4c103e1ea939e012ee79b`. Source currently shows matching names
   such as `handshake`, `time-limit` and `memory-limit`, but this is only an inspection
   finding. A03 used `--network=none`; do not weaken that regression sandbox to
   pretend it is a production worker connection.
7. Follow-up A05 inspection found `CPP23` absent from both `judge/fixtures/language_small.json`
   (18 languages) and `language_all.json` (59). The worker supports CPP23, but source
   handshake processing intersects advertised executors with existing database Language
   rows. Provision and verify matching CPP23 database/allowed-language metadata; loading
   a stock language fixture is not sufficient evidence of parity. No fixture was changed.
8. Keep actual website/bridge enrollment and browser AC/WA/result/score propagation
   as explicit B02/B03/B07–B09 acceptance tests. None ran in A04; a source-level
   protocol resemblance and matching problem identifiers do not prove compatibility.

[Source/asset/docs pins](source-pin.json), [support sources](support-sources.json),
[local environment](environment.json), [commands/exits](commands.json).
A05 may now map features against this inspected revision. No A06 or A09 work was performed.
