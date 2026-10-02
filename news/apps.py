from django.apps import AppConfig


class NewsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'news'

    def ready(self):
        # Import signal handlers so they get registered when the app loads.
        import news.signals  # noqa: F401
