from datetime import time, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from reservas.models import Sala, Reserva
from usuarios.models import Usuario


class Command(BaseCommand):
    help = "Carga salas, laboratorios y reservas ficticias de ejemplo (Dominio 4)"

    def handle(self, *args, **kwargs):
        salas_ejemplo = [
            {
                "nombre": "Laboratorio de Cómputo 1",
                "capacidad": 30,
                "equipo_disponible": "30 PCs Ubuntu/Windows, Proyector HD, Pizarra interactiva",
                "estado": Sala.ESTADO_DISPONIBLE,
            },
            {
                "nombre": "Laboratorio de Redes y Seguridad",
                "capacidad": 20,
                "equipo_disponible": "20 estaciones con Kali Linux, Switches Cisco, Routers",
                "estado": Sala.ESTADO_DISPONIBLE,
            },
            {
                "nombre": "Sala de Juntas A",
                "capacidad": 12,
                "equipo_disponible": "Pantalla Smart TV 65'', Sistema de videoconferencia",
                "estado": Sala.ESTADO_DISPONIBLE,
            },
            {
                "nombre": "Auditorio de Ingeniería",
                "capacidad": 100,
                "equipo_disponible": "Doble proyector, Sistema de audio profesional, 4 micrófonos",
                "estado": Sala.ESTADO_DISPONIBLE,
            },
        ]

        salas_creadas = []
        for s_info in salas_ejemplo:
            sala, created = Sala.objects.get_or_create(
                nombre=s_info["nombre"],
                defaults=s_info,
            )
            salas_creadas.append(sala)
            estado = "Creada" if created else "Ya existente"
            self.stdout.write(self.style.SUCCESS(f"[{estado}] Sala: {sala.nombre}"))

        # Crear reservas futuras de ejemplo solo si no existen reservas aún
        if not Reserva.objects.exists():
            gestor = Usuario.objects.filter(username="gestor").first()
            hoy = timezone.localdate()

            reservas_ejemplo = [
                {
                    "sala": salas_creadas[0],
                    "solicitante": "Prof. Carlos Ramírez",
                    "identificacion_solicitante": "1-1450-0321",
                    "correo_solicitante": "cramirez@utn.ac.cr",
                    "fecha": hoy + timedelta(days=2),
                    "hora_inicio": time(9, 0),
                    "hora_fin": time(11, 0),
                    "motivo": "Práctica de laboratorio ISW-622",
                    "estado": Reserva.ESTADO_ACTIVA,
                    "creado_por": gestor,
                },
                {
                    "sala": salas_creadas[1],
                    "solicitante": "Ing. Laura Méndez",
                    "identificacion_solicitante": "2-0789-0456",
                    "correo_solicitante": "lmendez@utn.ac.cr",
                    "fecha": hoy + timedelta(days=3),
                    "hora_inicio": time(14, 0),
                    "hora_fin": time(16, 30),
                    "motivo": "Taller de análisis de vulnerabilidades",
                    "estado": Reserva.ESTADO_ACTIVA,
                    "creado_por": gestor,
                },
            ]

            for r_info in reservas_ejemplo:
                reserva = Reserva.objects.create(**r_info)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"[Creada] Reserva {reserva.codigo} en '{reserva.sala.nombre}' para {reserva.fecha}"
                    )
                )
        else:
            self.stdout.write(
                self.style.WARNING(
                    "Ya existen reservas registradas; no se agregaron ejemplos."
                )
            )
