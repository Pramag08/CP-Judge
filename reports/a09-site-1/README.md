# A09 — supported DMOJ website startup

**PASS for the A09 startup gate, with the failed supplemental migration-drift
check retained below. Website-to-judge compatibility is NOT TESTED.** The saved
verification procedure actually ran through cleanup. No custom website feature,
converter change, judge rerun, commit or push was performed.

## Source and support decision

Selected official [DMOJ `django-52-upgrade`](https://github.com/DMOJ/online-judge/tree/604d60cfd764bc708b04ffd75b715a5398b91f8b),
commit **`604d60cfd764bc708b04ffd75b715a5398b91f8b`**, dated 2026-08-23,
GNU **AGPL v3**. Exact provenance, license hash, asset gitlink and four VCS
dependency commits are in [source-pin.json](source-pin.json). Its source checkout
was clean; there are **no local application patches**.

Official refs were checked first: [upstream-refs.txt](upstream-refs.txt).
Observed master remains A04's `6aaddea6aaeabf4927b83787714509ff9fff8897`, requiring
EOL Django 4.2. The official upgrade branch supplies Django 5.2/social-auth updates,
zoneinfo conversion, Django SQL join compatibility and `celery<6`: only five files,
28 additions/21 deletions versus master ([official-upgrade.diff](official-upgrade.diff)).
VNOI's inspected requirements still selected Django 4.2; a third-party fork or a
local framework port was unnecessary. **The selected branch is unmerged upstream
work, not a stable DMOJ release or a promise of upstream support.** Maintain its
exact pin, review upstream changes, and rerun this gate for updates.

Checked 28 October 2026: [Django's official table](https://www.djangoproject.com/download/)
lists 5.2.18 as the latest 5.2 LTS patch, with security support through April 2028;
4.2 ended support on 7 April 2026. The [5.2 Python matrix](https://docs.djangoproject.com/en/5.2/faq/install/)
includes Python 3.12 and adds 3.14 in 5.2.8. [Python 3.12](https://devguide.python.org/versions/)
has security maintenance through October 2028. We tested 3.12 rather than sharing
the host's 3.14 environment; third-party packages need their own validation.

[Django supports MariaDB through its MySQL backend](https://docs.djangoproject.com/en/5.2/ref/databases/#mariadb-notes).
[MariaDB 11.4](https://mariadb.org/about/#maintenance-policy) is maintained through
29 May 2029; [Node 22](https://nodejs.org/en/about/previous-releases) remains LTS;
[Redis Open Source 7.4](https://redis.io/docs/latest/operate/oss_and_stack/install/version-mgmt/)
lists maintenance through 1 December 2029. These are lifecycle findings, separate
from the tests below. All official references: [support-sources.json](support-sources.json).

## Tested environment and isolation

| Component | Actual tested version / evidence |
| --- | --- |
| Python / Django | **3.12.16 / 5.2.18**, Linux amd64 |
| Database / driver | **MariaDB 11.4.13 / mysqlclient 2.3.0**; utf8mb4, strict SQL mode |
| Background services | **Celery 5.6.3 / Redis server 7.4.12 / redis-py 8.1.0** |
| Asset tools | **Node 22.23.4 / npm 10.9.9**; Sass 1.106.1, PostCSS 8.5.32, CLI 12.0.0, Autoprefixer 10.6.2 |
| Browser libraries | jQuery 3.7.1, Ace 1.45.2; official site-assets gitlink `cba2efbf86e6e933704d8130fe256f2eab18621a` |
| Website image identity | `sha256:3ea8c0fbeb13e683ad0ba580b612c1c8987260f1617a6aafeca8aec751d9d99a` |

[base-pins.json](base-pins.json) pins the Python, MariaDB, Node and Redis images by
digest. [requirements.lock](requirements.lock) records all **86** installed Python
distributions, including pip and exact VCS commits; [install-report.json](install-report.json)
includes resolved artifact hashes. [package-lock.json](package-lock.json) records
the npm dependency graph/integrity; [os-packages.tsv](os-packages.tsv) records native
package versions. The second image used `pip install -r requirements.lock` and
`npm ci`; its resulting pip freeze is identical to the input lock.

The website runs as UID 10001 in its own image. Final replay dropped capabilities
and enabled no-new-privileges. MariaDB data and Redis data used disposable tmpfs;
all services used an internal Docker network with **no published host ports**.
No Docker socket, converter environment or private problem package was mounted.
Generated credentials stayed in ignored `build/` files with mode 0600. Containers,
their anonymous volumes and networks were removed after recording logs; the image
and ignored raw evidence remain. These controls are not a judge execution sandbox.

## Commands and observed results

[commands.json](commands.json) contains actual argument lists, exit statuses and
log paths for investigation and the complete saved-script replay. The locked image
build exited **0** ([build log](logs/build-locked.log)); the replay command exited **0**.
The first exploratory image's process exit was not retained after terminal context
resumption; its successful export is recorded, but it is not the final installation gate.

| Executed check | Observed result |
| --- | --- |
| Dependency installation / `python -m pip check` | Exit 0; no broken requirements; locked rebuild succeeded. |
| `python manage.py check --database default` | Exit 0, **one MariaDB constraint warning**, 51 upstream-silenced warnings. See limitations. |
| `python manage.py migrate --noinput` | Exit 0, **201 migrations applied** on a fresh MariaDB database. Reapply and `migrate --check`: exit 0, nothing pending. |
| `loaddata navbar language_small` and native CPP23 bootstrap | Exit 0. No demo admin/password fixture loaded; no Judge or RuntimeVersion records fabricated. |
| `python manage.py test judge --noinput -v 2` | Exit 0, **79 tests passed, no skips**; disposable `test_a09` database created/destroyed. |
| `compilemessages`, `compilejsi18n`, `collectstatic --noinput` | All exit 0; styles built in Node stage; **839 files collected**, two duplicate-path warnings. |
| `runserver ... --noreload` and real HTTP probe | Login GET 200, invalid password rejected, missing CSRF 403, valid login 302 and authenticated profile 200. Home/problems/contests/status/runtimes 200. |
| Local static HTTP probes | **15/15 HTTP 200**, nonempty expected asset types; all login CSS/JS references local, plus Ace/C++ mode, font, light/dark CSS and Select2. [Paths/hashes](http-results.json). |
| Redis cache and Celery | Cache round trip passed; worker started/pinged; upstream `judge.tasks.demo.success` actually completed through Redis broker/result backend. |
| Database dump/restore | Dump restored into disposable `a09_restore`; migration check and seeded account password/CPP23 metadata assertions exited 0. This is not an upgrade of an existing production database. |
| Supplemental `makemigrations --check --dry-run` | **FAILED, exit 1**; 11 upstream model-state differences. Audit generated **zero database-changing SQL statements**. It remains a failed diagnostic, not a passing migration check. |

Final replay logs are under [logs/replay/](logs/replay/), including
[migrations](logs/replay/migrate.log), [upstream tests](logs/replay/upstream-tests.log),
[HTTP server](logs/replay/http-log.log), [Celery](logs/replay/celery-log.log),
[backup/restore](logs/replay/backup-restore.log) and [restored data](logs/replay/restored-seed.log).
All earlier exploratory logs are retained too. Two exploratory HTTP probes failed:
one used `/login/` instead of the actual `/accounts/login/`; the second incorrectly
expected an offline executor on the participant runtime page. Source inspection of
`judge/views/language.py:LanguageList.get_queryset()` established its online-worker
filter. Corrected final probes passed; neither exploratory failure is counted as a pass.

## CPP23 representation and Phase B boundary

Both upstream language fixtures omit CPP23. [seed.py](seed.py) uses the existing
`judge/models/runtime.py:Language` model to create key **`CPP23`**, GNU C++23 name,
`C++23` short name, `c_cpp` Ace mode, `cpp` Pygments lexer and `.cpp` extension.
The disposable account's preferred language is verified as CPP23. This is setup
metadata, not a new executor, compiler change or custom website feature.

`judge/bridge/judge_handler.py` intersects worker executors with existing Language
keys; a future real handshake must match CPP23 and populate RuntimeVersion data.
This test deliberately has **zero Judge / RuntimeVersion records**. The stock
runtime page correctly hides offline languages from participants. A03's immutable
judge image still supports CPP23/GCC 16.2.0; neither checker nor solution was
downgraded to C++20, and that image was not modified or rerun.

Phase B must enroll the pinned worker, verify runtime/version advertisement and
allowed-language selection, install converted problem/checker data, submit through
the site/bridge, and assert limits, case verdicts, points and standings. Celery is a
background task worker; **it does not establish judge bridge compatibility**.

## Reproduce without touching the converter environment

Run from the repository root with Git, host Python stdlib and Docker available.
Use a new directory/prefix. Network is needed for source and image/package builds;
runtime verification uses its own internal network. `sg docker` is required in this
terminal to refresh Docker-group access; environments with normal Docker access can
run the enclosed command directly. No host pip/npm installation is needed.

```sh
git clone --depth 1 --branch django-52-upgrade https://github.com/DMOJ/online-judge.git build/a09-repeat-1/source
git -C build/a09-repeat-1/source fetch --depth 1 origin 604d60cfd764bc708b04ffd75b715a5398b91f8b
git -C build/a09-repeat-1/source checkout --detach 604d60cfd764bc708b04ffd75b715a5398b91f8b
git -C build/a09-repeat-1/source submodule update --init --recursive
python3 -B reports/a09-site-1/prepare_context.py --source build/a09-repeat-1/source --output build/a09-repeat-1/context
sg docker -c 'docker build --progress=plain -t cpjudge-a09-site:repeat1 build/a09-repeat-1/context'
sg docker -c 'python3 -B reports/a09-site-1/verify.py --work-dir build/a09-repeat-1/run --prefix cpjudge-a09-repeat1 --image cpjudge-a09-site:repeat1'
```

The saved preparer was exercised against the inspected checkout: its **669 context
files exactly match** the context used by the successful locked build. The saved
verifier actually ran with `build/a09-site-1/replay`, prefix `cpjudge-a09-replay1`,
image `cpjudge-a09-site:locked`, including cleanup. It refuses existing work
directories/Docker object names. It records the known failed drift diagnostic
separately and asserts its metadata-only/no-DDL analysis; other required checks
fail the run on nonzero exit. [Dockerfile](Dockerfile), [local settings](local_settings.py)
and all locks are supplied here; no private env file should be copied into reports.

## Remaining limitations and maintenance work

- **Unmerged official branch:** supported Python/Django/database lifecycles do not
  certify the entire DMOJ application or each older dependency. Pin and review this
  candidate; audit the legacy `webauthn<1`, `mistune<2`, `packaging<22` and
  `importlib-metadata<5` paths before enabling associated production features.
- **Migration drift:** related names, validators, choices, labels/help text differ
  from recorded state. [migration-audit.json](migration-audit.json) lists all 11
  changes and no-op SQL. No migration was generated/applied to conceal the issue.
  A future application-change baseline should reconcile state explicitly; timezone
  choices also depend on timezone data. No database schema redesign was needed.
- **MariaDB warning:** conditional `Class.unique_active_name` cannot be installed
  on MariaDB. Introspection confirms the existing unconditional unique `name`
  index remains enforced, which is stricter. Exact class/roster rules require A06
  design and later feature tests; this warning was neither silenced nor fixed here.
- **Deployment checks:** four warnings for missing SecurityMiddleware, insecure
  cookies and DEBUG. Upstream additionally silences 51 URL/field warnings; the
  unsilenced run records all 52 database-aware warnings. Database access during
  app initialization, pagination ordering, two duplicate static destinations and
  Celery legacy-setting deprecation remain in logs. The server is development
  `runserver`; production WSGI, proxy/TLS, backup policy and hardening are untested.
- **Browser/offline coverage:** actual HTTP and asset delivery were tested, not
  JavaScript execution, editor interaction, OAuth, registration/email identity,
  two-factor/WebAuthn or browser rendering. HIBP lookup fails on the isolated
  network and the existing common-password fallback allows the seeded local login;
  this does not certify complete offline operation. Non-login pages may still
  reference external resources, such as the timezone map.
- **Rebuild limits:** runtime Python/npm dependencies, source and base images are
  pinned, but apt repositories and isolated Python build backends are not fully
  archived/hash-locked. Native versions are recorded. This is a reproducible
  versioned setup procedure, not a claim of bit-identical or offline image rebuilds.
- **Phase B remains required:** no bridge/event daemon, judge enrollment, problem
  publication, real submission, verdict transport, scoring/standings, multi-worker
  recovery or load test ran. Optional live-event service dependencies are not part
  of the tested startup image. A03 evidence remains separate and unchanged.

[evidence.json](evidence.json), [result.json](result.json),
[preservation.json](preservation.json). A09 ends here; A06 and Phase B were not begun.
