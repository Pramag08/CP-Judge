# B01 — local DMOJ website/database baseline

**PASS for B01**, with retained limitations. [Final acceptance](result.json),
[independent review](review.json) and [preservation audit](preservation.json).
Website-to-judge compatibility is **NOT TESTED**;
B02, bridge/event/Celery services, worker enrollment and custom UI are outside B01.

## Reused stack and migration fix

Reuse A09's exact official website commit
`604d60cfd764bc708b04ffd75b715a5398b91f8b` (GNU AGPL v3), Python 3.12.16,
Django 5.2.18 and pinned MariaDB/Redis images. The B01 image derives from the
verified A09 image `sha256:3ea8c0fbeb13e683ad0ba580b612c1c8987260f1617a6aafeca8aec751d9d99a`.
No website package is installed in the converter venv, and no judge image or pin
changes. Exact current versions, image IDs, migration hashes and metadata are in
[baseline.json](baseline.json); all executed argv/exits/logs are in
[commands.json](commands.json); lifecycle exits are in [invocations.json](invocations.json).

The original A09 failure was reproduced before the fix: `makemigrations --check
--dry-run` exited 1. Eleven model fields differ from their historical migration
state: contest related_names, problem validator, checker choices/help text,
labels, translation/editor/math choices and timezone choices. Older migrations
snapshot older metadata; the upgrade also changed timezone enumeration from pytz
to zoneinfo. Current timezone choices were eagerly expanded from the machine's
available zoneinfo database, making a serialized snapshot environment-dependent.

The bounded fix is [the two-file source patch](../../patches/site/0001-stable-timezone-choices.patch)
and [new real forward migration 0153](../../deploy/site-local/migrations/0153_reconcile_model_metadata.py).
Retain/export make_timezones and use it as Profile.timezone's callable choices;
retain TIMEZONE for existing forms. The offered choices remain equal. Generate
11 AlterFields with Django and apply them normally after 0152. No previous
migration is edited/deleted, no fake migration or autodetector monkeypatch is
used, and no check is suppressed. On the selected MariaDB, sqlmigrate produces
11 no-op sections and no DDL. The migration still genuinely updates recorded
Django model state and is present in django_migrations: **202 applied total**.
The A09 historical failed diagnostic/report remains untouched.

This follows Django's supported [callable choices](https://docs.djangoproject.com/en/5.2/ref/models/fields/#choices)
and [versioned migration state](https://docs.djangoproject.com/en/5.2/topics/migrations/).
Keep the helper import path available to historical 0153; review any future
upstream migration-number collision against the source pin. See also
[delta attribution](../../patches/site/README.md).

## Start, stop and accounts

From the repository root, with Docker available:

```sh
python3 -B deploy/site-local/manage.py status
python3 -B deploy/site-local/manage.py start
python3 -B deploy/site-local/manage.py stop
python3 -B deploy/site-local/manage.py accounts
```

Local URL: **http://127.0.0.1:8000/**. All three services remain **RUNNING**
([observed state](services.json)); actual stop/start was verified. The lifecycle script refreshes this terminal's
Docker group using sg. Start/stop preserve the named disposable development data
volume `cpjudge-b01-data`; they do not reset passwords or remove history. Only
B01-labelled containers are managed. The website is unprivileged; DB/cache have
no published ports, and the web port binds 127.0.0.1 only. DB/cache use an internal
bridge. A separate website bridge permits Docker's localhost port publication.
This is a local development runserver, not a production or offline-LAN deployment.

Two accounts are created through native Django User/Profile/password hashing:
local development staff (superuser for the stock admin) and an ordinary participant
with no staff/superuser flags, groups or permissions. Their generated usernames
and passwords are in **build/b01-site-1/private/accounts.json**, mode 0600 inside
a 0700 directory. They are not included in reports/Git. Open that private file
locally and use the standard /accounts/login/ form. `accounts` prints the location
without printing credentials. Change a password interactively with:

```sh
sg docker -c 'docker exec -it cpjudge-b01-site python manage.py changepassword <username>'
```

Replace the placeholder locally; never put a password on argv. `verify` deliberately
reseeds both development account passwords from the private JSON, so it overwrites
interactive changes for those two accounts. Ordinary start/stop do not. B01 proves
stock authentication only; college-ID normalization, initial-password gating,
scoped author permissions and single-active-session replacement remain C tasks.

## Reproduce on a fresh local setup

Required baseline: exact clean A09 source in build/a09-site-1/site plus its locked
website/MariaDB/Redis images. If absent, follow [A09's source/submodule and locked
image build recipe](../a09-site-1/README.md), selecting these same paths/tag; don't
reuse its existing disposable verification output directory or overwrite evidence.
The lifecycle verifies the source commit, clean tree, image identity and pip lock.

```sh
python3 -B deploy/site-local/manage.py up
python3 -B deploy/site-local/manage.py browser
```

`up` refuses existing B01 containers/networks/volume or an occupied localhost
port; use start for the current setup. It stages the source patch in ignored
build, installs supplied 0153, builds a thin website image, applies migrations to
a fresh database, loads only native navbar/language fixtures, creates random
accounts, builds translations/JS catalogue and collects 839 static files. The
pinned A09 Sass/JS build output is reused, not falsely described as a new npm/Sass
build. `up` repeats the original/fixed drift comparisons deliberately to verify
the migration fix; it does not repeat A09's 79-test/background/backup exercise.

The separate browser image uses official Playwright; actual digest/version are
recorded in the browser report. The image includes browsers/system libraries;
the matching Python package is installed only in that isolated test image.
[Playwright Docker guidance](https://playwright.dev/python/docs/docker) explains
matching package/image versions. `deploy/site-local/browser-image.json` pins the
actual official image digest and matching Python package version. Browser auth
payloads/screenshots/errors remain
under ignored build/b01-site-1/browser/, not public reports. Only sanitized role
outcomes and asset/status measurements are copied into reports. The final browser
runs in host network mode against the exact localhost URL after a genuine stop/
start cycle; its request policy permits only that local website. Earlier internal-
URL evidence remains preserved separately. Browser images do not receive the
Docker socket, coordinator env or database credentials.

For an interrupted setup, `verify` can resume checks/fixtures/static collection
against the same B01 services without replacing the database. It is unnecessary
after a successful run unless a relevant change requires it. Every action gets
fresh logs; failed exploratory actions remain in commands.json.

## Verification, warnings and boundaries

- Dependency pip check/freeze equality, model-state consistency in fresh processes,
  genuine fresh migrations, reapply and migrate --check passed.
- Database audit confirms 202 migrations, unchanged original migration hashes,
  callable/list timezone equality, cache round trip and zero Judge/RuntimeVersion
  records. No judge is fabricated/enrolled.
- compilemessages, compilejsi18n and collectstatic passed. Two pre-existing static
  destination collisions remain recorded.
- System check exits 0 with the known MariaDB conditional-unique warning; the
  existing unconditional Class.name uniqueness is inspected and remains stricter.
  Unsilenced system/deployment checks retain all upstream warnings. Four deployment
  warnings (development DEBUG, secure cookies, SecurityMiddleware) remain expected
  local-development limitations, not production-readiness passes.
- Browser acceptance and independent review are recorded separately. No HTTP-only
  asset probe is called a browser test. Chromium rendered the styled native pages
  and completed all required forms. Known console errors are explicitly retained
  in [browser-limitations.json](browser-limitations.json): optional remote MathJax
  on profiles is blocked by the test's local-only request policy, and upstream
  admin's custom action-link helper references an undefined django namespace.
  Standard admin index/login and required account flows pass; custom shortcuts,
  profile/statement math and error-free JavaScript are not claimed. Neither issue
  was hidden with a stub or an unrelated template rewrite.

Initial setup failed while copying a private mode0600 host file as root inside
a capability-dropped container. The fix delivers it via stdin as the site UID;
no capabilities were added or credential permissions weakened. A subsequent
readiness check failed because Docker did not activate localhost port publishing
on an internal-only bridge. Internal HTTP200/cache connectivity isolated the cause;
adding the separate website bridge activated the existing 127.0.0.1 binding.
Those failures remain in commands.json; migrations were not rerun for routing.

Remaining scope: actual site-to-judge connection/verdicts/standings, production
hardening, broader account/session rules, custom UI and Run are untested.
Next task is B02, only when separately authorized. Do not infer compatibility
from this website/database milestone.
