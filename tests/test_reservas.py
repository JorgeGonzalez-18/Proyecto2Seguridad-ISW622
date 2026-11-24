"""
UTN-10 y RFD Dominio 4: Suite de pruebas automatizadas para Salas y Reservas.
Valida reglas de negocio (RN-4.1 a RN-4.3), detección de traslapes (RFD-4.3)
y control de acceso RBAC.
"""
from datetime import time, timedelta
import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone

from reservas.forms import ReservaForm
from reservas.models import Reserva, Sala

pytestmark = pytest.mark.django_db


@pytest.fixture
def sala_laboratorio():
    """Sala base para pruebas."""
    return Sala.objects.create(
        nombre="Laboratorio de Software 1",
        capacidad=30,
        equipo_disponible="30 PCs con Linux, Proyector",
        estado=Sala.ESTADO_DISPONIBLE,
    )


def _fecha_futura(dias=2):
    """Retorna una fecha con al menos 48 horas en el futuro para cumplir RN-4.3."""
    return timezone.localdate() + timedelta(days=dias)


# PRUEBAS DE REGLAS DE NEGOCIO Y FORMULARIO 

def test_rfd_4_3_deteccion_conflicto_traslape(sala_laboratorio):
    """
    RFD-4.3: El sistema debe rechazar automáticamente cualquier reserva
    que se traslape con otra reserva activa en la misma sala.
    """
    fecha = _fecha_futura(2)

    # 1. Crear primera reserva activa de 10:00 a 12:00
    Reserva.objects.create(
        sala=sala_laboratorio,
        solicitante="Profesor Carlos",
        identificacion_solicitante="101110111",
        correo_solicitante="carlos@utn.ac.cr",
        fecha=fecha,
        hora_inicio=time(10, 0),
        hora_fin=time(12, 0),
        estado=Reserva.ESTADO_ACTIVA,
    )

    # 2. Intentar crear una segunda reserva que se traslape (11:00 a 13:00)
    datos_traslape = {
        "sala": sala_laboratorio.id,
        "solicitante": "Estudiante María",
        "identificacion_solicitante": "202220222",
        "correo_solicitante": "maria@est.utn.ac.cr",
        "fecha": fecha,
        "hora_inicio": time(11, 0),
        "hora_fin": time(13, 0),
    }

    form = ReservaForm(data=datos_traslape)
    assert not form.is_valid(), "El formulario debió rechazar el traslape de horario"
    assert "Conflicto de horario" in str(form.errors)


def test_rn_4_1_hora_fin_posterior_a_inicio(sala_laboratorio):
    """
    RN-4.1: La hora de fin debe ser estrictamente posterior a la de inicio.
    """
    fecha = _fecha_futura(2)
    datos = {
        "sala": sala_laboratorio.id,
        "solicitante": "Solicitante Test",
        "identificacion_solicitante": "303330333",
        "correo_solicitante": "test@utn.ac.cr",
        "fecha": fecha,
        "hora_inicio": time(14, 0),
        "hora_fin": time(13, 0),  # Error: fin antes de inicio
    }
    form = ReservaForm(data=datos)
    assert not form.is_valid()
    assert "hora_fin" in form.errors


def test_rn_4_2_duracion_maxima_3_horas(sala_laboratorio):
    """
    RN-4.2: Una reserva dura como máximo 3 horas.
    """
    fecha = _fecha_futura(2)
    datos = {
        "sala": sala_laboratorio.id,
        "solicitante": "Solicitante Test",
        "identificacion_solicitante": "303330333",
        "correo_solicitante": "test@utn.ac.cr",
        "fecha": fecha,
        "hora_inicio": time(8, 0),
        "hora_fin": time(12, 0),  # Da Error: 4 horas de duración
    }
    form = ReservaForm(data=datos)
    assert not form.is_valid()
    assert "máximo 3 horas" in str(form.errors)


def test_rn_4_3_anticipacion_minima_24_horas(sala_laboratorio):
    """
    RN-4.3: Solo se permite reservar con al menos 24 horas de anticipación.
    """
    # Intentar reservar para el día de hoy (menos de 24 horas)
    fecha_invalida = timezone.localdate()
    datos = {
        "sala": sala_laboratorio.id,
        "solicitante": "Solicitante Urgente",
        "identificacion_solicitante": "404440444",
        "correo_solicitante": "urgente@utn.ac.cr",
        "fecha": fecha_invalida,
        "hora_inicio": time(10, 0),
        "hora_fin": time(12, 0),
    }
    form = ReservaForm(data=datos)
    assert not form.is_valid()
    assert "24 horas de anticipación" in str(form.errors)


def test_rfd_4_4_cancelar_reserva_libera_horario(cliente_gestor, sala_laboratorio):
    """
    RFD-4.4: Cancelar una reserva libera la franja horaria inmediatamente
    permitiendo que otro usuario reserve ese mismo horario.
    """
    fecha = _fecha_futura(3)

    # 1. Crear reserva inicial
    reserva = Reserva.objects.create(
        sala=sala_laboratorio,
        solicitante="Docente Ana",
        identificacion_solicitante="505550555",
        correo_solicitante="ana@utn.ac.cr",
        fecha=fecha,
        hora_inicio=time(9, 0),
        hora_fin=time(11, 0),
        estado=Reserva.ESTADO_ACTIVA,
    )

    # 2. Gestor cancela la reserva vía POST
    url_cancelar = reverse("reservas:cancelar_reserva", kwargs={"codigo": reserva.codigo})
    resp = cliente_gestor.post(url_cancelar)
    assert resp.status_code == 302

    reserva.refresh_from_db()
    assert reserva.estado == Reserva.ESTADO_CANCELADA

    # 3. Verificar que la franja ahora está libre para otra persona
    datos_nueva = {
        "sala": sala_laboratorio.id,
        "solicitante": "Nuevo Solicitante",
        "identificacion_solicitante": "606660666",
        "correo_solicitante": "nuevo@utn.ac.cr",
        "fecha": fecha,
        "hora_inicio": time(9, 0),
        "hora_fin": time(11, 0),
    }
    form = ReservaForm(data=datos_nueva)
    assert form.is_valid(), "El horario debió quedar liberado tras la cancelación"


# PRUEBAS DE CONTROL DE ACCESO 

def test_auditor_bloqueado_crear_reserva_403(cliente_auditor, sala_laboratorio):
    """
    UTN-06: El rol Auditor es de solo lectura.
    Si intenta crear una reserva por POST, recibe HTTP 403 Forbidden.
    """
    url = reverse("reservas:crear_reserva")
    resp = cliente_auditor.post(url, {
        "sala": sala_laboratorio.id,
        "solicitante": "Auditor Tramposo",
        "identificacion_solicitante": "707770777",
        "correo_solicitante": "auditor@utn.ac.cr",
        "fecha": _fecha_futura(2),
        "hora_inicio": "10:00",
        "hora_fin": "12:00",
    })
    assert resp.status_code == 403


def test_rfd_4_5_reporte_ocupacion_permisos(cliente_superadmin, cliente_auditor, cliente_gestor):
    """
    RFD-4.5: SuperAdmin y Auditor acceden al reporte de ocupación (200).
    El Gestor de reservas es rechazado con HTTP 403 Forbidden.
    """
    url = reverse("reservas:reporte_ocupacion")

    # SuperAdmin: Permitido (200)
    assert cliente_superadmin.get(url).status_code == 200

    # Auditor: Permitido (200)
    assert cliente_auditor.get(url).status_code == 200

    # Gestor de reservas: Rechazado (403)
    assert cliente_gestor.get(url).status_code == 403