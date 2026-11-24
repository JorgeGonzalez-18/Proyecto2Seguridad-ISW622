"""
RFD-4.5: Pruebas del reporte de ocupación semanal (cálculo en horas y acceso por permiso).
"""
from datetime import date, time

import pytest
from django.urls import reverse

from reservas.models import Reserva, Sala
from reservas.reportes import HORAS_DISPONIBLES_SEMANA, calcular_ocupacion_semanal, inicio_de_semana

pytestmark = pytest.mark.django_db

# Semana fija: lunes 2026-03-02 a domingo 2026-03-08
LUNES = date(2026, 3, 2)


@pytest.fixture
def sala_a():
    return Sala.objects.create(nombre="Lab A", capacidad=30, equipo_disponible="PCs")


@pytest.fixture
def sala_b():
    return Sala.objects.create(nombre="Lab B", capacidad=20, equipo_disponible="Proyector")


def _reserva(sala, fecha, inicio, fin, estado=Reserva.ESTADO_ACTIVA, n=0):
    return Reserva.objects.create(
        sala=sala, solicitante=f"Solicitante {n}", identificacion_solicitante=f"1-000{n}",
        correo_solicitante=f"s{n}@u.ac.cr", fecha=fecha, hora_inicio=inicio, hora_fin=fin,
        estado=estado,
    )


def _fila(datos, sala):
    return next(f for f in datos["filas"] if f["sala"].pk == sala.pk)


def test_inicio_de_semana_es_lunes():
    assert inicio_de_semana(date(2026, 3, 8)) == LUNES  # domingo
    assert inicio_de_semana(LUNES) == LUNES


def test_horas_y_porcentaje_por_sala(sala_a, sala_b):
    _reserva(sala_a, LUNES, time(8), time(10), n=1)                       # 2 h lunes
    _reserva(sala_a, date(2026, 3, 4), time(9, 30), time(11), n=2)        # 1.5 h miércoles
    _reserva(sala_b, date(2026, 3, 7), time(13), time(16), n=3)           # 3 h sábado
    datos = calcular_ocupacion_semanal(date(2026, 3, 5))                  # cualquier día de la semana
    a, b = _fila(datos, sala_a), _fila(datos, sala_b)
    assert a["horas_usadas"] == 3.5 and a["total_reservas"] == 2
    assert a["porcentaje"] == round(3.5 / HORAS_DISPONIBLES_SEMANA * 100, 1)
    assert a["horas_por_dia"][0]["horas"] == 2 and a["horas_por_dia"][2]["horas"] == 1.5
    assert b["horas_usadas"] == 3 and b["horas_por_dia"][5]["horas"] == 3
    assert datos["total_horas"] == 6.5 and datos["total_reservas"] == 3


def test_canceladas_no_cuentan_y_fuera_de_semana_se_ignoran(sala_a):
    _reserva(sala_a, LUNES, time(8), time(10), estado=Reserva.ESTADO_CANCELADA, n=1)
    _reserva(sala_a, date(2026, 3, 9), time(8), time(10), n=2)   # semana siguiente
    _reserva(sala_a, date(2026, 3, 1), time(8), time(10), n=3)   # semana anterior
    datos = calcular_ocupacion_semanal(LUNES)
    assert _fila(datos, sala_a)["horas_usadas"] == 0
    assert datos["total_reservas"] == 0


def test_finalizadas_si_cuentan(sala_a):
    _reserva(sala_a, LUNES, time(8), time(9), estado=Reserva.ESTADO_FINALIZADA, n=1)
    assert _fila(calcular_ocupacion_semanal(LUNES), sala_a)["horas_usadas"] == 1


def test_sala_sin_reservas_aparece_en_cero(sala_a):
    fila = _fila(calcular_ocupacion_semanal(LUNES), sala_a)
    assert fila["horas_usadas"] == 0 and fila["porcentaje"] == 0


def test_porcentaje_no_supera_100(sala_a):
    for i in range(7):
        _reserva(sala_a, date(2026, 3, 2 + i % 6), time(7), time(19), n=i)  # 12 h/día, 7 reservas
    assert _fila(calcular_ocupacion_semanal(LUNES), sala_a)["porcentaje"] <= 100


# ---------- Control de acceso (UTN-05: permiso «Ver reportes») ----------
def test_superadmin_y_auditor_ven_el_reporte(cliente_superadmin, cliente_auditor, sala_a):
    _reserva(sala_a, LUNES, time(8), time(10), n=1)
    for c in (cliente_superadmin, cliente_auditor):
        r = c.get(reverse("reservas:reporte_ocupacion"), {"fecha": "2026-03-04"})
        assert r.status_code == 200
        assert "Lab A" in r.content.decode()


def test_gestor_recibe_403_en_reporte(cliente_gestor):
    assert cliente_gestor.get(reverse("reservas:reporte_ocupacion")).status_code == 403


def test_anonimo_redirige_al_login_en_reporte(client):
    r = client.get(reverse("reservas:reporte_ocupacion"))
    assert r.status_code == 302 and reverse("login") in r["Location"]


def test_reporte_fecha_invalida_no_rompe(cliente_auditor):
    r = cliente_auditor.get(reverse("reservas:reporte_ocupacion"), {"fecha": "no-es-fecha"})
    assert r.status_code == 200


def test_reporte_no_expone_datos_personales_del_solicitante(cliente_auditor, sala_a):
    _reserva(sala_a, LUNES, time(8), time(10), n=7)
    html = cliente_auditor.get(reverse("reservas:reporte_ocupacion"), {"fecha": "2026-03-02"}).content.decode()
    assert "Solicitante 7" not in html and "1-0007" not in html and "s7@u.ac.cr" not in html
