# A09 base identity is checked by manage.py before build. No dependency reinstall.
ARG SITE_BASE=cpjudge-a09-site:locked
FROM ${SITE_BASE}
COPY --chown=site:site choices.py /app/judge/models/choices.py
COPY --chown=site:site profile.py /app/judge/models/profile.py
COPY --chown=site:site 0153_reconcile_model_metadata.py /app/judge/migrations/0153_reconcile_model_metadata.py
COPY --chown=site:site local_settings.py /app/dmoj/local_settings.py
LABEL cpjudge.task=B01 cpjudge.site.commit=604d60cfd764bc708b04ffd75b715a5398b91f8b
