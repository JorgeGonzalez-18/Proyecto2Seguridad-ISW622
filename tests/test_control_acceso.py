"""
UTN-10 / TC-06, TC-07 y TC-08: Control de acceso (403) y CSRF.
"""
import pytest
from django.test import Client
from django.urls import reverse

from usuarios.models import Rol, Usuario


@pytest.mark.django_db
def test_tc06_auditor_no_puede_editar_roles(cliente_auditor, roles):
    """TC-06: El Auditor recibe 403 al intentar editar un rol."""
    rol = roles["Gestor de reservas"]
    url = reverse("editar_rol", args=[rol.pk])

    assert cliente_auditor.get(url).status_code == 403

    respuesta = cliente_auditor.post(url, {"nombre": "Hackeado", "puede_borrar": "on"})
    assert respuesta.status_code == 403
    rol.refresh_from_db()
    assert rol.nombre == "Gestor de reservas"


@pytest.mark.django_db
def test_tc06_pagina_403_limpia_sin_trazas(cliente_auditor):
    """TC-06b: La página 403 no muestra trazas ni información interna."""
    respuesta = cliente_auditor.get(reverse("lista_roles"))

    contenido = respuesta.content.decode()
    assert respuesta.status_code == 403
    for fuga in ("Traceback", "PermissionDenied", "settings.py", 'File "'):
        assert fuga not in contenido


@pytest.mark.django_db
def test_tc07_gestor_no_puede_eliminar_usuarios(cliente_gestor, auditor):
    """TC-07: El Gestor de reservas recibe 403 al eliminar un usuario por POST."""
    respuesta = cliente_gestor.post(reverse("eliminar_usuario", args=[auditor.pk]))

    assert respuesta.status_code == 403
    assert Usuario.objects.filter(pk=auditor.pk).exists()


@pytest.mark.django_db
def test_tc07_anonimo_no_puede_eliminar_usuarios(client, auditor):
    """TC-07b: Sin sesión, el POST de eliminación no borra nada."""
    respuesta = client.post(reverse("eliminar_usuario", args=[auditor.pk]))

    assert respuesta.status_code in (302, 403)
    assert Usuario.objects.filter(pk=auditor.pk).exists()


@pytest.mark.django_db
def test_tc08_csrf_crear_rol_sin_token(superadmin):
    """TC-08: Un POST modificador sin token CSRF responde 403."""
    cliente = Client(enforce_csrf_checks=True)
    cliente.force_login(superadmin)

    respuesta = cliente.post(reverse("crear_rol"), {"nombre": "RolCSRF", "descripcion": "x"})

    assert respuesta.status_code == 403
    assert not Rol.objects.filter(nombre="RolCSRF").exists()


@pytest.mark.django_db
def test_tc08_csrf_eliminar_usuario_sin_token(superadmin, gestor):
    """TC-08b: Eliminar un usuario sin token CSRF tampoco funciona."""
    cliente = Client(enforce_csrf_checks=True)
    cliente.force_login(superadmin)

    respuesta = cliente.post(reverse("eliminar_usuario", args=[gestor.pk]))

    assert respuesta.status_code == 403
    assert Usuario.objects.filter(pk=gestor.pk).exists()