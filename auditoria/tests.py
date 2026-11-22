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


class CambiosRolAuditoriaTests(TestCase):
    def setUp(self):
        from usuarios.models import Rol

        self.rol_admin = Rol.objects.create(nombre="SuperAdmin", puede_crear=True)
        self.rol_aud = Rol.objects.create(nombre="Auditor")
        self.admin = Usuario.objects.create_user(
            username="root", password="Clave-Segura-123", identificacion="9-9999-9999",
            nombre_completo="Root", rol=self.rol_admin,
        )
        self.otro = Usuario.objects.create_user(
            username="bob", password="Clave-Segura-123", identificacion="2-2222-2222",
            nombre_completo="Bob",
        )
        LogAuditoria.objects.all().delete()
        self.client.force_login(self.admin)
        LogAuditoria.objects.all().delete()

    def test_editar_permisos_de_rol_registra_quien_y_que(self):
        self.client.post(
            reverse("editar_rol", args=[self.rol_aud.pk]),
            {"nombre": "Auditor", "descripcion": "", "puede_ver_reportes": "on"},
        )
        log = LogAuditoria.objects.get(tipo_evento=LogAuditoria.TIPO_CAMBIO_ROL)
        self.assertEqual(log.username_intentado, "root")
        self.assertEqual(log.usuario_afectado, "Rol: Auditor")
        self.assertIn("Ver reportes", log.detalle)

    def test_asignar_rol_a_usuario_registra_cambio(self):
        self.client.post(
            reverse("editar_usuario", args=[self.otro.pk]),
            {"username": "bob", "nombre_completo": "Bob", "identificacion": "2-2222-2222",
             "email": "", "rol": self.rol_aud.pk, "is_active": "on"},
        )
        log = LogAuditoria.objects.get(tipo_evento=LogAuditoria.TIPO_CAMBIO_ROL)
        self.assertEqual(log.usuario_afectado, "bob")
        self.assertEqual(log.username_intentado, "root")
        self.assertIn("Auditor", log.detalle)

    def test_guardar_sin_cambios_no_registra(self):
        self.otro.nombre_completo = "Bob Nuevo"
        self.otro.save()
        self.assertFalse(
            LogAuditoria.objects.filter(tipo_evento=LogAuditoria.TIPO_CAMBIO_ROL).exists()
        )


class Acceso403AuditoriaTests(TestCase):
    def setUp(self):
        from usuarios.models import Rol

        rol = Rol.objects.create(nombre="Auditor")
        self.auditor = Usuario.objects.create_user(
            username="aud", password="Clave-Segura-123", identificacion="3-3333-3333",
            nombre_completo="Aud", rol=rol,
        )
        LogAuditoria.objects.all().delete()

    def test_403_registra_ruta_usuario_e_ip(self):
        self.client.force_login(self.auditor)
        r = self.client.get(reverse("lista_roles"), REMOTE_ADDR="10.9.9.9")
        self.assertEqual(r.status_code, 403)
        log = LogAuditoria.objects.get(tipo_evento=LogAuditoria.TIPO_ACCESO_DENEGADO)
        self.assertEqual(log.username_intentado, "aud")
        self.assertEqual(log.ruta, reverse("lista_roles"))
        self.assertEqual(log.ip, "10.9.9.9")

    def test_respuesta_200_no_registra(self):
        self.client.force_login(self.auditor)
        self.client.get(reverse("lista_usuarios"))
        self.assertFalse(
            LogAuditoria.objects.filter(tipo_evento=LogAuditoria.TIPO_ACCESO_DENEGADO).exists()
        )

    def test_csrf_fallido_se_registra_como_403(self):
        from django.test import Client

        c = Client(enforce_csrf_checks=True)
        r = c.post(reverse("login"), {"username": "aud", "password": "x"})
        self.assertEqual(r.status_code, 403)
        self.assertTrue(
            LogAuditoria.objects.filter(tipo_evento=LogAuditoria.TIPO_ACCESO_DENEGADO).exists()
        )
