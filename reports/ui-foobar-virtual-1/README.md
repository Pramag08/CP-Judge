# foobar header and read-only contest results — 2026-11-03

**PASS for the requested local UI and virtual-entry gate.** The supplied root `Foobarlogo.png` was copied to the scoped static namespace, displayed in the existing header slot, and used as the browser icon. Site, Open Graph, page and admin titles use `foobar`; upstream DMOJ footer attribution remains. The header orders Contests before authorized-only Author Contests. The account button displays down/up chevrons with its closed/open state, exposes `aria-expanded`, and works with Enter, Space and Escape. The role switcher remains absent. The stock contest-list Admin tab is removed; author management remains under Author Contests.

Past contest rows and native ended-contest detail pages use a GET Results link to the existing ranking URL only when `can_see_own_scoreboard` allows it. The native join route rejects all ended contest joins with 403 before upstream virtual creation. Existing participations and official standings remain. The live browser opened `/contest/icap111a/ranking/` and rejected both private `/contest/navproof26/ranking/` and ended `/contest/b10b11local1/ranking/` for the participant; a CSRF-valid POST to `/contest/icap111a/join` returned 403. `icap111a` participation count was 2 before and after the repeat browser proof. No judging, rejudge, migration, commit or push.

| Command/check | Exit | Observed result |
| --- | ---: | --- |
| `docker cp deploy/phase-c/cpjudge/. cpjudge-b01-site:/app/cpjudge` | 0 | Template/asset/route overlay staged. |
| `docker cp deploy/phase-c/native_settings.py cpjudge-b01-site:/app/dmoj/cpj_native_settings.py` | 0 | Title settings staged. A mistaken preliminary copy to the separate integration settings path was immediately restored from `deploy/phase-c/integration_settings.py` (exit 0) before reload/tests. |
| `docker exec cpjudge-b01-site python manage.py collectstatic --noinput` | 0 | 2 files copied, 946 unchanged; logo served from `/static/cpjudge/foobar-logo.png`. |
| `python3 -B deploy/phase-c/c13_bundle.py reload` | 0 | Local HTTP/Celery reload completed. |
| Pinned local Chromium `cpjudge-b01-browser:local1` running ignored `build/ui-foobar-1/browser.py` with the preserved C18 fixture | 0 | Staff and participant header/title/logo/favicon/menu/keyboard checks, tab scope/order, attribution, permitted Results, private ranking denial, ended-join 403. Ignored result and screenshots: `build/ui-foobar-1/results/`. Initial diagnostic runs used an old credential fixture and case-sensitive assertion; final run passed. |
| Read-only ORM count before and after repeat browser proof | 0 each | `icap111a` had 2 participations both times. |
| `docker exec --user 1000:1000 cpjudge-b01-site python manage.py test cpjudge.entry_tests --settings=dmoj.cpj_integration_settings --keepdb --noinput -v 1` | 0 | 14 tests passed; one existing MariaDB conditional-unique warning. |
| `python3 -B -m py_compile deploy/phase-c/native_settings.py deploy/phase-c/cpjudge/entries.py`; `git diff --check` | 0 each | Syntax and whitespace pass. |

Scope: local existing templates/assets and a narrow native join guard. Existing virtual records are preserved; no attempt was made to remove their historical labels or alter official scores. Other contest permissions remain enforced by the existing server routes. Next task: H03 or another explicitly requested MVP task.
