from django.test import TestCase
from django.urls import reverse

from usuarios.models import Usuario

from .models import LogAuditoria


class LoginAuditoriaTests(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            username="alice", password="Clave-Segura-123", identificacion="1-1111-1111",
            nombre_completo="Alice Test",
        )

    def test_login_exitoso_registra_log(self):
        self.client.post(
            reverse("login"),
            {"username": "alice", "password": "Clave-Segura-123"},
            REMOTE_ADDR="10.1.2.3",
        )
        log = LogAuditoria.objects.get(tipo_evento=LogAuditoria.TIPO_LOGIN_EXITOSO)
        self.assertEqual(log.usuario, self.usuario)
        self.assertEqual(log.ip, "10.1.2.3")

    def test_login_fallido_registra_log_sin_password(self):
        self.client.post(
            reverse("login"),
            {"username": "alice", "password": "incorrecta"},
            HTTP_X_FORWARDED_FOR="203.0.113.7, 10.0.0.1",
        )
        log = LogAuditoria.objects.get(tipo_evento=LogAuditoria.TIPO_LOGIN_FALLIDO)
        self.assertEqual(log.username_intentado, "alice")
        self.assertEqual(log.ip, "203.0.113.7")
        self.assertNotIn("incorrecta", log.detalle)

    def test_login_fallido_usuario_inexistente(self):
        self.client.post(reverse("login"), {"username": "' OR '1'='1", "password": "x"})
        self.assertEqual(
            LogAuditoria.objects.filter(tipo_evento=LogAuditoria.TIPO_LOGIN_FALLIDO).count(), 1
        )
