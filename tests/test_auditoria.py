"""
UTN-09: Pruebas de integración del registro de auditoría (pytest).
Usa las fixtures de tests/conftest.py (roles base y un usuario por rol).
"""
import pytest
from django.test import Client
from django.urls import reverse

from auditoria.models import LogAuditoria
from tests.conftest import PASSWORD_PRUEBA

pytestmark = pytest.mark.django_db


def _logs(tipo):
    return LogAuditoria.objects.filter(tipo_evento=tipo)


# ---------- Inicios de sesión ----------
def test_login_exitoso_se_audita_con_ip(auditor):
    Client().post(
        reverse("login"),
        {"username": auditor.username, "password": PASSWORD_PRUEBA},
        REMOTE_ADDR="192.0.2.10",
    )
    log = _logs(LogAuditoria.TIPO_LOGIN_EXITOSO).get()
    assert log.usuario == auditor
    assert log.ip == "192.0.2.10"


def test_login_fallido_se_audita_sin_guardar_password(auditor):
    Client().post(
        reverse("login"),
        {"username": auditor.username, "password": "clave-incorrecta-xyz"},
        HTTP_X_FORWARDED_FOR="198.51.100.4",
    )
    log = _logs(LogAuditoria.TIPO_LOGIN_FALLIDO).get()
    assert log.username_intentado == auditor.username
    assert log.ip == "198.51.100.4"
    assert "clave-incorrecta-xyz" not in (log.detalle + log.ruta)


def test_sql_injection_en_login_se_audita_y_no_autentica(roles):
    r = Client().post(reverse("login"), {"username": "' OR '1'='1", "password": "' OR '1'='1"})
    assert "_auth_user_id" not in r.wsgi_request.session
    assert _logs(LogAuditoria.TIPO_LOGIN_FALLIDO).count() == 1
    assert not _logs(LogAuditoria.TIPO_LOGIN_EXITOSO).exists()


# ---------- Accesos denegados ----------
def test_403_se_audita_con_ruta_usuario_e_ip(cliente_auditor, auditor):
    r = cliente_auditor.get(reverse("lista_roles"), REMOTE_ADDR="192.0.2.77")
    assert r.status_code == 403
    log = _logs(LogAuditoria.TIPO_ACCESO_DENEGADO).get()
    assert log.ruta == reverse("lista_roles")
    assert log.username_intentado == auditor.username
    assert log.ip == "192.0.2.77"


def test_gestor_no_puede_eliminar_usuarios_y_queda_registrado(cliente_gestor, auditor):
    r = cliente_gestor.post(reverse("eliminar_usuario", args=[auditor.pk]))
    assert r.status_code == 403
    assert _logs(LogAuditoria.TIPO_ACCESO_DENEGADO).count() == 1


def test_csrf_faltante_se_audita_como_403(superadmin):
    c = Client(enforce_csrf_checks=True)
    c.force_login(superadmin)
    r = c.post(reverse("crear_rol"), {"nombre": "Intruso"})
    assert r.status_code == 403
    assert _logs(LogAuditoria.TIPO_ACCESO_DENEGADO).exists()


# ---------- Cambios de roles y permisos ----------
def test_editar_permisos_de_rol_registra_quien_a_quien_y_que(cliente_superadmin, superadmin, roles):
    rol = roles["Auditor"]
    LogAuditoria.objects.all().delete()
    cliente_superadmin.post(
        reverse("editar_rol", args=[rol.pk]),
        {"nombre": rol.nombre, "descripcion": rol.descripcion,
         "puede_crear": "on", "puede_ver_reportes": "on"},
    )
    log = _logs(LogAuditoria.TIPO_CAMBIO_ROL).get()
    assert log.username_intentado == superadmin.username
    assert log.usuario_afectado == "Rol: Auditor"
    assert "Crear" in log.detalle


def test_cambiar_rol_de_usuario_se_audita(cliente_superadmin, superadmin, gestor, roles):
    LogAuditoria.objects.all().delete()
    cliente_superadmin.post(
        reverse("editar_usuario", args=[gestor.pk]),
        {"username": gestor.username, "nombre_completo": gestor.nombre_completo,
         "identificacion": gestor.identificacion, "email": gestor.email,
         "rol": roles["Auditor"].pk, "is_active": "on"},
    )
    log = _logs(LogAuditoria.TIPO_CAMBIO_ROL).get()
    assert log.usuario_afectado == gestor.username
    assert log.username_intentado == superadmin.username
    assert "Auditor" in log.detalle


# ---------- Panel de auditoría (solo SuperAdmin) ----------
def test_panel_solo_superadmin(cliente_superadmin, cliente_auditor, cliente_gestor):
    url = reverse("panel_auditoria")
    assert cliente_superadmin.get(url).status_code == 200
    assert cliente_auditor.get(url).status_code == 403
    assert cliente_gestor.get(url).status_code == 403


def test_panel_anonimo_redirige_a_login():
    r = Client().get(reverse("panel_auditoria"))
    assert r.status_code == 302
    assert reverse("login") in r["Location"]


def test_panel_filtra_por_tipo_y_escapa_html(cliente_superadmin):
    LogAuditoria.objects.create(
        tipo_evento=LogAuditoria.TIPO_LOGIN_FALLIDO,
        username_intentado="<script>alert(1)</script>",
    )
    r = cliente_superadmin.get(reverse("panel_auditoria"), {"tipo": LogAuditoria.TIPO_LOGIN_FALLIDO})
    contenido = r.content.decode()
    assert "<script>alert(1)</script>" not in contenido
    assert "&lt;script&gt;" in contenido


# ---------- Integridad del log ----------
def test_log_es_inmutable():
    log = LogAuditoria.objects.create(tipo_evento=LogAuditoria.TIPO_LOGIN_EXITOSO)
    log.detalle = "alterado"
    with pytest.raises(PermissionError):
        log.save()
