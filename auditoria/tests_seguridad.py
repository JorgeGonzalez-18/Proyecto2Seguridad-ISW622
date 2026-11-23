from django.test import Client, TestCase, override_settings
from django.urls import reverse

from usuarios.models import Rol, Usuario


class HeadersSeguridadTests(TestCase):
    """UTN-08: Encabezados HTTP de seguridad presentes en las respuestas."""

    def test_headers_en_login(self):
        r = self.client.get(reverse("login"))
        self.assertEqual(r.headers.get("X-Frame-Options"), "DENY")
        self.assertEqual(r.headers.get("X-Content-Type-Options"), "nosniff")
        csp = r.headers.get("Content-Security-Policy", "")
        self.assertIn("default-src 'self'", csp)
        self.assertIn("object-src 'none'", csp)
        self.assertIn("frame-ancestors 'none'", csp)

    def test_headers_tambien_en_403_y_404(self):
        self.assertEqual(self.client.get("/no-existe/").headers.get("X-Content-Type-Options"), "nosniff")
        rol = Rol.objects.create(nombre="Auditor")
        u = Usuario.objects.create_user(
            username="h1", password="Clave-Segura-123", identificacion="5-5555-5555",
            nombre_completo="H", rol=rol,
        )
        self.client.force_login(u)
        r = self.client.get(reverse("lista_roles"))
        self.assertEqual(r.status_code, 403)
        self.assertEqual(r.headers.get("X-Frame-Options"), "DENY")
        self.assertIn("default-src", r.headers.get("Content-Security-Policy", ""))

    @override_settings(SECURE_HSTS_SECONDS=31536000)
    def test_hsts_sobre_https(self):
        r = self.client.get(reverse("login"), secure=True)
        hsts = r.headers.get("Strict-Transport-Security", "")
        self.assertIn("max-age=31536000", hsts)
        self.assertIn("includeSubDomains", hsts)


class CsrfTests(TestCase):
    """UTN-07d: POST sin token CSRF es rechazado con 403."""

    def setUp(self):
        rol = Rol.objects.create(nombre="SuperAdmin")
        self.admin = Usuario.objects.create_user(
            username="c1", password="Clave-Segura-123", identificacion="4-4444-4444",
            nombre_completo="C", rol=rol,
        )
        self.otro = Usuario.objects.create_user(
            username="victima", password="Clave-Segura-123", identificacion="4-4444-0000",
            nombre_completo="V",
        )

    def test_post_login_sin_token_rechazado(self):
        c = Client(enforce_csrf_checks=True)
        r = c.post(reverse("login"), {"username": "c1", "password": "Clave-Segura-123"})
        self.assertEqual(r.status_code, 403)

    def test_eliminar_usuario_sin_token_rechazado_y_no_borra(self):
        c = Client(enforce_csrf_checks=True)
        c.force_login(self.admin)
        r = c.post(reverse("eliminar_usuario", args=[self.otro.pk]))
        self.assertEqual(r.status_code, 403)
        self.assertTrue(Usuario.objects.filter(pk=self.otro.pk).exists())

    def test_formularios_incluyen_token(self):
        self.client.force_login(self.admin)
        for nombre in ("crear_rol",):
            r = self.client.get(reverse(nombre))
            self.assertContains(r, "csrfmiddlewaretoken")
