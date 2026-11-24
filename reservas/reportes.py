"""
RFD-4.5: Cálculo del reporte de ocupación por sala y por semana.

La ocupación se mide en HORAS de uso real (no solo en cantidad de reservas):
  ocupación % = horas reservadas en la semana / horas disponibles en la semana

Se cuentan las reservas ACTIVAS y FINALIZADAS; las CANCELADAS liberan la
franja (RFD-4.4) y por eso no cuentan como ocupación.
"""
from datetime import date, datetime, timedelta

from .models import Reserva, Sala

# Horario operativo de salas y laboratorios (Lunes a Sábado, 07:00 - 19:00)
HORA_APERTURA = 7
HORA_CIERRE = 19
DIAS_OPERATIVOS = 6
HORAS_DISPONIBLES_DIA = HORA_CIERRE - HORA_APERTURA
HORAS_DISPONIBLES_SEMANA = HORAS_DISPONIBLES_DIA * DIAS_OPERATIVOS

ESTADOS_QUE_OCUPAN = (Reserva.ESTADO_ACTIVA, Reserva.ESTADO_FINALIZADA)

NOMBRES_DIAS = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]


def inicio_de_semana(fecha: date) -> date:
    """Devuelve el lunes de la semana de `fecha`."""
    return fecha - timedelta(days=fecha.weekday())


def duracion_horas(reserva) -> float:
    inicio = datetime.combine(reserva.fecha, reserva.hora_inicio)
    fin = datetime.combine(reserva.fecha, reserva.hora_fin)
    return max((fin - inicio).total_seconds() / 3600, 0)


def calcular_ocupacion_semanal(fecha_ref: date) -> dict:
    """
    Agrupa las reservas por sala para la semana (lunes a domingo) que contiene
    `fecha_ref` y calcula horas de uso, ocupación % y horas por día.
    """
    lunes = inicio_de_semana(fecha_ref)
    domingo = lunes + timedelta(days=6)

    reservas = Reserva.objects.filter(
        fecha__range=(lunes, domingo), estado__in=ESTADOS_QUE_OCUPAN
    ).only("sala_id", "fecha", "hora_inicio", "hora_fin")

    por_sala = {}
    for r in reservas:
        datos = por_sala.setdefault(r.sala_id, {"horas_dia": [0.0] * 7, "cantidad": 0})
        datos["horas_dia"][r.fecha.weekday()] += duracion_horas(r)
        datos["cantidad"] += 1

    filas = []
    total_horas = 0.0
    total_reservas = 0
    for sala in Sala.objects.all():
        datos = por_sala.get(sala.id, {"horas_dia": [0.0] * 7, "cantidad": 0})
        horas = round(sum(datos["horas_dia"]), 2)
        porcentaje = min(100, round(horas / HORAS_DISPONIBLES_SEMANA * 100, 1))
        total_horas += horas
        total_reservas += datos["cantidad"]
        filas.append(
            {
                "sala": sala,
                "total_reservas": datos["cantidad"],
                "horas_usadas": horas,
                "porcentaje": porcentaje,
                "porcentaje_barra": int(porcentaje),
                "horas_por_dia": [
                    {"dia": NOMBRES_DIAS[i], "horas": round(h, 2)}
                    for i, h in enumerate(datos["horas_dia"])
                ],
            }
        )

    return {
        "inicio_semana": lunes,
        "fin_semana": domingo,
        "semana_anterior": lunes - timedelta(days=7),
        "semana_siguiente": lunes + timedelta(days=7),
        "filas": filas,
        "total_reservas": total_reservas,
        "total_horas": round(total_horas, 2),
        "horas_disponibles_sala": HORAS_DISPONIBLES_SEMANA,
        "dias_nombres": NOMBRES_DIAS,
    }
