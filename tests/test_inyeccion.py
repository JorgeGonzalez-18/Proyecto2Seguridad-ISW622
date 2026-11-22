"""
UTN-10 / TC-01 y TC-02: Pruebas de inyección SQL.
"""
import pytest
from django.urls import NoReverseMatch, reverse

PAYLOADS_SQLI = [
    "' OR '1'='1",
    "' OR '1'='1' --",
    "admin'--",
    "' UNION SELECT username, password FROM usuarios_usuario --",
]

ERRORES_SQL = ["OperationalError", "ProgrammingError", "syntax error", "Traceback"]


@pytest.mark.django_db
@pytest.mark.parametrize("payload", PAYLOADS_SQLI)
def test_tc01_sqli_login_no_autentica(client, superadmin, payload):
    """TC-01: Un payload de SQLi en el login no debe iniciar sesión."""
    respuesta = client.post(reverse("login"), {"username": payload, "password": payload})

    assert respuesta.status_code == 200, "El login debe volver a mostrarse, no redirigir"
    assert "_auth_user_id" not in client.session, "La inyección SQL inició sesión"
    contenido = respuesta.content.decode()
    for error in ERRORES_SQL:
        assert error not in contenido


@pytest.mark.django_db
def test_tc01_sqli_password_con_usuario_real(client, superadmin):
    """TC-01b: Usuario real con contraseña inyectada tampoco autentica."""
    client.post(
        reverse("login"),
        {"username": superadmin.username, "password": "' OR '1'='1"},
    )
    assert "_auth_user_id" not in client.session


def _url_busqueda():
    """Busca la ruta de búsqueda de salas/reservas (app del integrante 2)."""
    for nombre in ("buscar_salas", "lista_salas", "buscar_reservas", "lista_reservas"):
        try:
            return reverse(nombre)
        except NoReverseMatch:
            continue
    return None


@pytest.mark.django_db
@pytest.mark.parametrize("payload", PAYLOADS_SQLI)
def test_tc02_sqli_busqueda_salas(cliente_gestor, payload):
    """TC-02: SQLi en el parámetro de búsqueda no provoca error ni fuga de datos."""
    url = _url_busqueda()
    if url is None:
        pytest.skip("Pendiente: la app reservas/ aún no expone la búsqueda")

    respuesta = cliente_gestor.get(url, {"q": payload})

    assert respuesta.status_code == 200
    contenido = respuesta.content.decode()
    for error in ERRORES_SQL:
        assert error not in contenido