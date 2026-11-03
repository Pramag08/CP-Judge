# B01 bounded follow-up

**PASS for the requested fixes and recorded UI direction.** Original
[B01 evidence](../b01-site-1/README.md) is unchanged. The local site remains at
http://127.0.0.1:8000/; existing website, DB and Redis containers were retained.
No actual package import, judging or standings behavior was tested.

| Requested work | Result / evidence |
| --- | --- |
| Approved UI direction | [Contract](../../docs/contracts/ui-direction.md): keep DMOJ horizontal navigation, centered content, compact tables, sidebar styling and footer; adapt templates, no separate frontend. Eligible-contest home and simplified individual/role scope remain requirements. Foobar logo-only slot approved; asset absent, not invented/installed. |
| Admin loading | [Source patch](../../patches/site/0002-local-math-admin-loading.patch) uses WPadmin's guaranteed real global jQuery for shortcuts. [Package compatibility delta](../../patches/site/0003-wpadmin-actions-initializer.patch) lets Django's actual actions.js initialize selection controls, removing obsolete duplicate `.actions()` setup. No namespace/plugin stubs or error suppression. |
| Local math | MathJax **3.2.2**, exact npm lock/integrity, complete prebuilt JS/extensions/fonts and Apache-2.0 LICENSE; [file manifest](math-assets.json), [lock](../../deploy/site-local/assets/package-lock.json). Profile/content, raw statements and Martor preview resolve local files and wait for real startup completion. |
| Static destinations | [Resolution](static-resolution.json): canonical Django jquery.init.js, package default WPadmin CSS and namespaced site CSS each have one source. Original site CSS bytes retained; old WPadmin bootstrap retained outside finders. Collected output is no longer re-imported as source. 947 static files collected with no collision warning. |
| Verify versus reset | `manage.py verify` checks dependencies/migrations/accounts without loading fixtures, applying migrations or setting passwords. Password hashes remain byte-identical, including a changed temporary password. `reset-accounts` is explicit, password-only, and tested on temporary identities only. |

## What actually ran

[commands.json](commands.json) records argv, UTC timestamps, actual exit statuses
and fresh logs. [Lifecycle/test invocations](invocations.json) include failed
explorations as well as final successes; [result.json](result.json) and
[preservation.json](preservation.json) summarize acceptance.

- The native admin login, dashboard, user change/list and contest list were opened
  in Chromium. Canonical Django/real global jQuery, native master selection and
  shortcut POST+CSRF were checked. The shortcut request was intercepted **before
  the backend**: no rerating/rejudging action was executed or certified.
- Native authentication, participant admin denial and password change passed.
  After ordinary verification, the changed temporary password still logged in,
  its old password was rejected, and all pre-existing account hashes were exact.
  Explicit reset was separately invoked with a private fixture credential file;
  browser acceptance/rejection reversed correctly. Existing users/profiles were
  never reset or edited. Temporary identities/pages were removed.
- The final math browser report (`browser-math-final-*.json`) verifies three
  equations each in a real profile, native `problem/raw.html` rendered from
  synthetic context and native preview/loader. Inline/display fractions, roots,
  matrix/integral and local color autoload were exercised. Exact counts prevent
  duplicate rendering; statement/preview blue output is checked. Profile has no
  colored-expression fixture. Local JS/font/extension requests returned 200 and
  page errors were zero. Screenshots were visually inspected and remain private.
- Browser requests outside localhost were blocked before transport. Only legacy
  Gravatar decoration attempts occurred; no external math request occurred.
  This is not a full-site offline or all-admin-feature claim.
- Final [runtime audit](runtime-final.json) checks deployed source and every math
  asset hash, unique static sources, source/collected JS equality, unchanged 0153,
  202 consistent migrations and removed fixtures. Existing users/profiles and
  Problem/Contest/Submission/Judge/RuntimeVersion counts match the pre-test state.

The first browser pass used weaker math assertions; visual review caught duplicate
raw equations. The final math report supersedes those earlier rendering assertions,
while earlier authentication/reset evidence remains valid. Both shared loaders
now await automatic startup; the asynchronous preview waits before targeted
manual typesetting. No repeated typesetting races or fake renderer were retained.

## Local commands and reproducibility

```sh
python3 -B deploy/site-local/manage.py start
python3 -B deploy/site-local/manage.py stop
python3 -B deploy/site-local/manage.py verify
python3 -B deploy/site-local/manage.py accounts
# Explicit operator request only; reapplies the private development credential file:
python3 -B deploy/site-local/manage.py reset-accounts
```

Ordinary actions log to reports/site-local-runs/ (or CPJ_SITE_REPORT_DIR), preserving
the original B01 report. `accounts` identifies the ignored mode0600 credential
file; its initial/reset values do not override passwords changed later. Stop/start
preserves the DB and current overlay. No reset occurs on verification/start.

For a **fresh B01 baseline**, retain the original setup/migration recipe, then:

```sh
python3 -B deploy/site-local/followup.py bundle
python3 -B deploy/site-local/followup.py apply
```

Bundle uses A09's pinned Node image and `npm ci --ignore-scripts`; the thin
Dockerfile adds only the bounded overlay and MathJax assets, without Python/Sass
reinstallation or a UI rebuild. Apply refuses unknown edits to the targeted
native files, saves existing settings, keeps other settings/B02 work, and restarts
only the exact development web process. Database/cache/background services are not
replaced. The current running container retains its B01 base plus recorded overlay;
`Dockerfile.followup` is the reproducible image artifact, not a secret-bearing
container commit. Existing migrations and dependency pins are unchanged.

Focused test replay requires fresh ignored output/evidence directories; set
CPJ_FOLLOWUP_WORK and CPJ_FOLLOWUP_REPORT to absolute build/... and reports/... paths.
The actions are fixtures → browser → check-changed → verify → check-changed → browser
→ reset-fixtures → check-reset → browser → cleanup. This creates temporary native
auth/math fixtures, not an imported/judged problem. Never point replay at old reports.
The final stricter renderer-only check uses math-browser after fixtures. Raw
credentials, saved account state, screenshots and detailed browser failures stay
under ignored build/. No dependency/judge/converter suite was rerun.

## Retained warnings and failures

Unsilenced system checks retain upstream warnings, including MariaDB's unsupported
conditional Class uniqueness (existing unconditional name uniqueness remains).
`check --deploy` still reports SecurityMiddleware, development DEBUG and insecure
cookie settings. No production-hardening warning was removed or silenced.

Failed setup/test attempts are retained: missing JS catalogue after changing
STATIC_ROOT (regenerated); a synthetic RequestFactory lacking middleware context
(replaced with a real Client-populated request); preview startup race; obsolete
WPadmin actions initialization; ambiguous hidden logout/master-toggle test
selectors; and one unregistered final-audit CLI action (exit 2, no runtime mutation).
Final checks passed after correction. No unrelated expensive baseline was repeated.

Remaining: approved Foobar asset and later UI/backend tasks; full offline/LAN and
production hardening are unverified. The homepage direction is recorded, not
implemented here. No B02 work, actual import/judging/standings, commit or push.
