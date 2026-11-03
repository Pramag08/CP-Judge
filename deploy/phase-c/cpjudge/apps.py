from django.apps import AppConfig

class CPJudgeConfig(AppConfig):
    name = 'cpjudge'
    default_auto_field = 'django.db.models.AutoField'

    def ready(self):
        from . import sessions  # noqa: F401

        from django.conf import settings
        if getattr(settings, 'CPJ_NATIVE', False):
            from .native import install
            install()
