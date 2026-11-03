# Navigation and branding simplification — 2026-11-03

**PASS for the requested local UI.** The designated `b01-staff` record remained active, staff, superuser and explicitly `Identity.is_author=True`, with its existing ten active scoped grants. No account, grant or backend policy changed. The top-right account greeting no longer displays “Author ▾” or acts as a role-mode selector; the existing author contest link and role-menu Create contest / Manage contests / imports links remain conditional on author identity. The same Chromium session opened `/contests/`, the participant-facing `/contest/icap111a`, author creation/list/draft and `/contest/navproof26/import/`. A participant saw no author links and direct author/import routes returned 403/404.

Reused DMOJ templates and settings now render exactly `Contests-CPJudge` as plain text in the top-left home-link slot, the site-name/page-title suffix and WPadmin title. The contest-list tab override omits Calendar; the shared footer omits the UI-language form. The upstream “proudly powered by DMOJ” link remains as attribution. No global replacement, dependency, native module, submission form or sandbox change. The native participant `/problem/pv000000000000000001/submit` page still rendered its `#id_language` picker and allowed CPP23 to be selected; no POST or new submission was made.

Checks and exits (repository root):

| Command/check | Exit | Observed result |
| --- | ---: | --- |
| `python3 -B deploy/site-local/manage.py status` | 0 | b03/b02/services/site/DB/Redis running. |
| Targeted `docker cp` of `native_settings.py`, `base.html`, `site-logo-fragment.html` and `contest/contest-list-tabs.html` to their existing site paths | 0 each | Local template/settings overlay staged. Initial `docker exec mkdir -p` attempts exited 1 because that directory is not writable from inside the running container; `docker cp` staged the new override directory successfully, with no data change. |
| `python3 -B deploy/phase-c/c13_bundle.py reload` | 0 | HTTP/Celery reloaded; bridge, worker and data retained. |
| Pinned local Chromium `cpjudge-b01-browser:local1` running `build/branding-nav-1/browser.py` | 0 | Exact header text/no logo image, site and admin titles, author/participant access, no Calendar or footer language form, retained attribution and native CPP23 selection. Raw private browser inputs/result under ignored `build/branding-nav-1/`; final result contains no credentials. |
| `docker exec cpjudge-b01-site python manage.py check` | 0 | No issues (51 silenced). |
| Read-only ORM identity/count query | 0 | Existing flags and grants intact; 32 imports, 4 versions, 14 contests, 37 submissions, 2 private author tests and zero official contest rows for those tests. |
| `python3 -B -m py_compile deploy/phase-c/native_settings.py` and `git diff --check` | 0 | Syntax and whitespace pass. |

The browser test was read-only after login. Its relevant URL checks: `/contests/`, `/contest/icap111a`, `/author/contests/create/`, `/author/contests/`, `/author/contests/navproof26/`, `/contest/navproof26/import/`, `/admin/`, and `/problem/pv000000000000000001/submit` at `http://127.0.0.1:8000`. Current enabled language on that native submission form is CPP23; this check does not add another language or judge a submission. Existing one-active-session policy means the browser logins can replace older sessions. H03's broader combined journey remains pending. No commit or push.
