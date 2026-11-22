"""
UTN-10: Fixtures compartidas para la suite de pruebas de seguridad.
Crea los 3 roles base (comando crear_roles) y un usuario por rol.
"""
import pytest
from django.core.management import call_command
from django.test import Client

from usuarios.models import Rol, Usuario

PASSWORD_PRUEBA = "ClaveSegura#2026"


@pytest.fixture
def roles(db):
    call_command("crear_roles", verbosity=0)
    return {r.nombre: r for r in Rol.objects.all()}


def _crear_usuario(username, rol, identificacion, nombre):
    return Usuario.objects.create_user(
        username=username,
        password=PASSWORD_PRUEBA,
        email=f"{username}@pruebas.local",
        nombre_completo=nombre,
        identificacion=identificacion,
        rol=rol,
    )


@pytest.fixture
def superadmin(roles):
    return _crear_usuario(
        "t_superadmin", roles["SuperAdmin"], "900000001", "Super Admin Pruebas"
    )


@pytest.fixture
def auditor(roles):
    return _crear_usuario(
        "t_auditor", roles["Auditor"], "900000002", "Auditor Pruebas"
    )


@pytest.fixture
def gestor(roles):
    return _crear_usuario(
        "t_gestor", roles["Gestor de reservas"], "900000003", "Gestor Pruebas"
    )


@pytest.fixture
def cliente_superadmin(superadmin):
    c = Client()
    c.force_login(superadmin)
    return c


@pytest.fixture
def cliente_auditor(auditor):
    c = Client()
    c.force_login(auditor)
    return c


@pytest.fixture
def cliente_gestor(gestor):
    c = Client()
    c.force_login(gestor)
    return c