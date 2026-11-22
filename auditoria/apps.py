from django.apps import AppConfig


class AuditoriaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'auditoria'
    verbose_name = 'Módulo de Auditoría y Seguridad'

    def ready(self):
        # Conectar las señales automáticas para registrar logins y eventos
        import auditoria.signals

        