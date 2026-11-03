# Local DMOJ website deltas

Base: official DMOJ/online-judge `django-52-upgrade`, commit
`604d60cfd764bc708b04ffd75b715a5398b91f8b`, GNU AGPL v3. Preserve upstream
LICENSE/source attribution; this directory is a bounded overlay, not vendored
ownership of DMOJ. A09 source/lock/license evidence remains unchanged.

B01 applies `0001-stable-timezone-choices.patch` to a private staging copy and
adds `deploy/site-local/migrations/0153_reconcile_model_metadata.py` after 0152.
Keep the original migrations byte for byte. `make_timezones` remains importable;
Profile.timezone uses the supported callable choices API. The existing TIMEZONE
list remains for forms/templates, with the same values. The new migration
records eleven existing model-metadata differences; MariaDB sqlmigrate produces
no schema-changing SQL. No fake migration, history rewrite, state-detector
monkeypatch or check suppression is used.

Runtime source/metadata pins and setup evidence: reports/b01-site-1/.
Future upstream updates must review the overlay and resolve any new 0153
number collision explicitly; do not apply it blindly to a different source pin.

B01 follow-up retains the migration patch/0153 unchanged. New bounded deltas:
`0002-local-math-admin-loading.patch` updates three native loader/template paths
and the shared admin shortcut's real jQuery dependency. MathJax 3.2.2 uses the
pinned npm lock and retains its Apache-2.0 LICENSE. The site's WPadmin CSS is
moved intact to an explicit `cpjudge/` namespace; WPadmin's older jquery.init.js
is retained outside finders so Django's real bootstrap is canonical.

`0003-wpadmin-actions-initializer.patch` removes only the obsolete duplicate
`.actions()` initialization from the installed WPadmin change-list template;
Django 5.2's actual actions.js initializes its native Actions API automatically.
WPadmin's visual HTML remains. The package remains pinned to A09's exact
`dmoj-wpadmin` VCS revision `dfafe1b20d69e2e0f8cf625fecbb957414040b80`; original
package files and attribution are retained outside static finders. No synthetic
django namespace or jQuery actions shim is introduced.

B02 is COMPLETE — PASS with independent review. The bounded
`0004-event-set-iteration.patch` changes the native event daemon's follower/poller
iteration to the pinned simplesets snapshot API (`array().forEach`), preserving
removal during callbacks. [Acceptance/configuration](../../reports/b02-services-1/README.md)
and [latest service status](../../reports/b02-status-1/README.md). It establishes
service readiness only at the B02 boundary; worker enrollment and integrated
judging were untested at that stage. Later B03/B07 evidence is separate.

B06/B07 add bounded, reproducible runtime overlays without changing source pins:
`deploy/site-local/statement_overlay.py` keeps the native problem layout and adds
a private fixed-name sanitized stylesheet route plus receipt-checked fragment
filter; it removes only the existing Semantic UI remote font import from source
and collected CSS. Original package scripts/CSS are never trusted directly.
`bridge_observe.py` adds passive sanitized tracing after original native send and
callback handling; packet fields, scheduling, limits and results are unchanged.
Upstream source/licensing remains DMOJ's; new adapters are local integration code.
Evidence: reports/b06-statement-1/ and reports/b07-submission-1/. The actual private
CPP23 reference AC is now established for103 cases; broader judging/standings,
publication/readiness and production gates remain untested.
