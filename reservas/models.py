import uuid
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class Sala(models.Model):
    """
    RFD-4.1: Catálogo de salas y laboratorios.
    Registra salas con nombre, capacidad, equipo disponible y estado.
    """
    ESTADO_DISPONIBLE = 'DISPONIBLE'
    ESTADO_MANTENIMIENTO = 'MANTENIMIENTO'

    ESTADOS_SALA = [
        (ESTADO_DISPONIBLE, 'Disponible'),
        (ESTADO_MANTENIMIENTO, 'En Mantenimiento'),
    ]

    nombre = models.CharField(
        max_length=100, 
        unique=True, 
        verbose_name="Nombre de la sala/laboratorio"
    )
    capacidad = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(500)],
        verbose_name="Capacidad (personas)"
    )
    equipo_disponible = models.TextField(verbose_name="Equipo disponible")
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS_SALA,
        default=ESTADO_DISPONIBLE,
        verbose_name="Estado de la sala"
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Sala / Laboratorio"
        verbose_name_plural = "Salas y Laboratorios"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} (Capacidad: {self.capacidad})"


def generar_codigo_reserva():
    """Genera un código alfanumérico único para la reserva (ej: RES-7F2A8B1C)."""
    return f"RES-{uuid.uuid4().hex[:8].upper()}"


class Reserva(models.Model):
    """
    UTN-03 y RFD-4.2: Entidad principal Reserva.
    Campos obligatorios del enunciado:
    Código (alfanumérico), sala, solicitante, fecha, hora de inicio, hora de fin, estado.
    Dato sensible a proteger: datos personales del solicitante y calendario de uso.
    """
    ESTADO_ACTIVA = 'ACTIVA'
    ESTADO_CANCELADA = 'CANCELADA'
    ESTADO_FINALIZADA = 'FINALIZADA'

    ESTADOS_RESERVA = [
        (ESTADO_ACTIVA, 'Activa'),
        (ESTADO_CANCELADA, 'Cancelada'),
        (ESTADO_FINALIZADA, 'Finalizada'),
    ]

    codigo = models.CharField(
        max_length=20,
        unique=True,
        default=generar_codigo_reserva,
        editable=False,
        verbose_name="Código de Reserva"
    )
    sala = models.ForeignKey(
        Sala,
        on_delete=models.PROTECT,
        related_name="reservas",
        verbose_name="Sala o Laboratorio"
    )
    # Datos del solicitante (dato sensible a proteger del Red Team)
    solicitante = models.CharField(max_length=150, verbose_name="Nombre del solicitante")
    identificacion_solicitante = models.CharField(max_length=30, verbose_name="Cédula / Identificación")
    correo_solicitante = models.EmailField(verbose_name="Correo institucional del solicitante")

    fecha = models.DateField(verbose_name="Fecha de reserva")
    hora_inicio = models.TimeField(verbose_name="Hora de inicio")
    hora_fin = models.TimeField(verbose_name="Hora de fin")
    motivo = models.TextField(blank=True, verbose_name="Motivo académico / uso")

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS_RESERVA,
        default=ESTADO_ACTIVA,
        verbose_name="Estado de la reserva"
    )

    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reservas_creadas",
        verbose_name="Registrado por"
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Reserva"
        verbose_name_plural = "Reservas"
        ordering = ['-fecha', 'hora_inicio']

    def __str__(self):
        return f"[{self.codigo}] {self.sala.nombre} - {self.fecha} ({self.hora_inicio} a {self.hora_fin}) - {self.estado}"