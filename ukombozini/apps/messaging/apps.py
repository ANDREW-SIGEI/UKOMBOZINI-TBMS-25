from django.apps import AppConfig

class MessagingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ukombozini.apps.messaging'

    def ready(self):
        import ukombozini.apps.messaging.signals  # noqa
