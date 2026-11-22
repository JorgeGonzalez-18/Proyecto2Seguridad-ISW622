"""
UTN-10 / TC-03 y TC-04: Pruebas de Cross-Site Scripting (XSS).
"""
import pytest
from django.urls import reverse

from usuarios.models import Usuario

PAYLOAD_XSS = "<script>alert('xss')</script>"
PAYLOAD_XSS_IMG = '<img src=x onerror="alert(1)">'


@pytest.mark.django_db
@pytest.mark.parametrize("payload", [PAYLOAD_XSS, PAYLOAD_XSS_IMG])
def test_tc03_xss_reflejado_en_parametros_url(client, payload):
    """TC-03: Un script en la URL (?next= y ?q=) no se refleja sin escapar."""
    respuesta = client.get(reverse("login"), {"next": payload, "q": payload})

    assert respuesta.status_code == 200
    assert payload not in respuesta.content.decode()


@pytest.mark.django_db
def test_tc03_xss_reflejado_en_usuario_del_login(client):
    """TC-03b: El username que el login devuelve al formulario sale escapado."""
    respuesta = client.post(reverse("login"), {"username": PAYLOAD_XSS, "password": "x"})

    contenido = respuesta.content.decode()
    assert PAYLOAD_XSS not in contenido
    assert "&lt;script&gt;" in contenido


@pytest.mark.django_db
def test_tc04_xss_almacenado_en_nombre_de_usuario(cliente_superadmin, roles):
    """TC-04: Un script guardado en nombre_completo se muestra escapado en la lista."""
    Usuario.objects.create_user(
        username="victima_xss",
        password="ClaveSegura#2026",
        nombre_completo=PAYLOAD_XSS,
        identificacion="900000099",
        rol=roles["Gestor de reservas"],
    )

    respuesta = cliente_superadmin.get(reverse("lista_usuarios"))

    contenido = respuesta.content.decode()
    assert respuesta.status_code == 200
    assert PAYLOAD_XSS not in contenido
    assert "&lt;script&gt;" in contenido