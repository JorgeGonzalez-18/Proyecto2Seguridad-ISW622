"""
UTN-10 / TC-10: Encabezados HTTP de seguridad. Extra: UTN-02 (Argon2id).
"""
import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_tc10_encabezados_de_seguridad(client):
    """TC-10: La respuesta incluye CSP, nosniff y X-Frame-Options."""
    respuesta = client.get(reverse("login"))

    assert respuesta.headers.get("X-Content-Type-Options") == "nosniff"
    assert respuesta.headers.get("X-Frame-Options") == "DENY"

    csp = respuesta.headers.get("Content-Security-Policy")
    assert csp, "Falta el encabezado Content-Security-Policy"
    assert "default-src 'self'" in csp
    assert "object-src 'none'" in csp


@pytest.mark.django_db
def test_tc10_no_expone_tecnologia_del_servidor(client):
    """TC-10b: No se filtra la tecnología del servidor en los encabezados."""
    respuesta = client.get(reverse("login"))
    assert "X-Powered-By" not in respuesta.headers


@pytest.mark.django_db
def test_extra_contrasenas_con_argon2id(gestor):
    """Extra (UTN-02): La contraseña se guarda con Argon2id, no con MD5/SHA."""
    assert gestor.password.startswith("argon2$argon2id$")