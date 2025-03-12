from django.apps import AppConfig


class ConfigUiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'config_ui'
    verbose_name = 'Конфигурация пользовательского интерфейса'
