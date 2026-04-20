from django.apps import AppConfig


class FieldsConfig(AppConfig):
    name = 'fields'

class FieldsConfig(AppConfig):
    name = 'fields'

    def ready(self):
        import fields.signals