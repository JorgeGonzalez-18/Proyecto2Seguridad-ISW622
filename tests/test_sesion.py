"""
UTN-10 / TC-05 y TC-09: Expiración de sesión y cookies seguras.
"""
import time
from unittest import mock

import pytest
from django.conf import settings
from django.urls import reverse

from tests.conftest import PASSWORD_PRUEBA


def test_tc05_configuracion_expiracion_60_segundos():
    """TC-05a: La sesión está configurada para vencer a los 60 segundos."""
    assert settings.SESSION_COOKIE_AGE == 60
    assert settings.SESSION_SAVE_EVERY_REQUEST is True
    assert getattr(settings, "TIEMPO_INACTIVIDAD_SEGUNDOS", None) == 60


@pytest.mark.django_db
def test_tc05_sesion_expira_tras_60_segundos_de_inactividad(cliente_gestor):
    """TC-05b: Tras 61 s sin actividad, la siguiente petición pide login de nuevo."""
    # Primera petición: el middleware registra la última actividad
    assert cliente_gestor.get(reverse("inicio")).status_code == 200

    # Simulamos que pasaron 61 segundos
    futuro = time.time() + 61
    with mock.patch("usuarios.middleware.time.time", return_value=futuro):
        respuesta = cliente_gestor.get(reverse("inicio"))

    assert respuesta.status_code == 302
    assert reverse("login") in respuesta.url
    assert "_auth_user_id" not in cliente_gestor.session


@pytest.mark.django_db
def test_tc05_sesion_sigue_activa_antes_de_60_segundos(cliente_gestor):
    """TC-05c: Con 30 s de inactividad la sesión sigue activa."""
    cliente_gestor.get(reverse("inicio"))

    futuro = time.time() + 30
    with mock.patch("usuarios.middleware.time.time", return_value=futuro):
        respuesta = cliente_gestor.get(reverse("inicio"))

    assert respuesta.status_code == 200


@pytest.mark.django_db
def test_tc09_cookie_de_sesion_segura(client, gestor):
    """TC-09: La cookie de sesión es HttpOnly, SameSite y no lleva datos en claro."""
    respuesta = client.post(
        reverse("login"),
        {"username": gestor.username, "password": PASSWORD_PRUEBA},
    )
    assert respuesta.status_code == 302, "El login con credenciales válidas debe redirigir"

    cookie = respuesta.cookies[settings.SESSION_COOKIE_NAME]
    assert cookie["httponly"] is True
    assert cookie["samesite"].lower() in ("lax", "strict")

    for dato_sensible in (gestor.username, PASSWORD_PRUEBA, gestor.identificacion):
        assert dato_sensible not in cookie.value

    # Ni la contraseña ni su hash se guardan en los datos de la sesión
    datos_sesion = str(dict(client.session))
    assert PASSWORD_PRUEBA not in datos_sesion
    assert gestor.password not in datos_sesion


def test_tc09_cookie_csrf_protegida():
    """TC-09b: La cookie CSRF también tiene HttpOnly y SameSite."""
    assert settings.CSRF_COOKIE_HTTPONLY is True
    assert settings.CSRF_COOKIE_SAMESITE in ("Lax", "Strict")