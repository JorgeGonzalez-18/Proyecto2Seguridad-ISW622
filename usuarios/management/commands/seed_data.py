"""
Integrante 4: Datos semilla listos para el pentest.
Crea 1 SuperAdmin, 1 Auditor, 1 Gestor de reservas y, si ya existe la app
reservas/, 5 salas con reservas de ejemplo.

Uso:  python manage.py seed_data
"""
from datetime import datetime, time, timedelta

from django.apps import apps
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from usuarios.models import Rol, Usuario

USUARIOS_SEMILLA = [
    {
        "username": "superadmin",
        "password": "SuperAdmin#2026",
        "nombre_completo": "Sofía Administradora",
        "identificacion": "100000001",
        "email": "superadmin@reservas.local",
        "rol": "SuperAdmin",
    },
    {
        "username": "auditor",
        "password": "Auditor#2026",
        "nombre_completo": "Andrés Auditor",
        "identificacion": "100000002",
        "email": "auditor@reservas.local",
        "rol": "Auditor",
    },
    {
        "username": "gestor",
        "password": "Gestor#2026",
        "nombre_completo": "Gabriela Gestora",
        "identificacion": "100000003",
        "email": "gestor@reservas.local",
        "rol": "Gestor de reservas",
    },
]

SALAS_SEMILLA = [
    {"nombre": "Laboratorio de Cómputo 1", "capacidad": 30, "equipo": "30 PCs, proyector"},
    {"nombre": "Laboratorio de Redes", "capacidad": 20, "equipo": "Routers, switches, rack"},
    {"nombre": "Sala de Reuniones A", "capacidad": 10, "equipo": "Pantalla 65\", videoconferencia"},
    {"nombre": "Auditorio Principal", "capacidad": 120, "equipo": "Sonido, proyector, micrófonos"},
    {"nombre": "Laboratorio de Electrónica", "capacidad": 25, "equipo": "Osciloscopios, fuentes"},
]


class Command(BaseCommand):
    help = "Carga usuarios de prueba (uno por rol) y salas con reservas de ejemplo"

    @transaction.atomic
    def handle(self, *args, **options):
        call_command("crear_roles", verbosity=0)
        self.stdout.write(self.style.SUCCESS("Roles base verificados"))

        gestor = None
        for datos in USUARIOS_SEMILLA:
            usuario = self._crear_usuario(datos)
            if datos["rol"] == "Gestor de reservas":
                gestor = usuario

        if apps.is_installed("reservas"):
            self._crear_salas_y_reservas(gestor)
        else:
            self.stdout.write(
                self.style.WARNING("La app 'reservas' aún no existe: se omiten salas y reservas")
            )

        self.stdout.write(self.style.SUCCESS("Datos semilla listos"))

    def _crear_usuario(self, datos):
        rol = Rol.objects.get(nombre=datos["rol"])
        usuario, creado = Usuario.objects.get_or_create(
            username=datos["username"],
            defaults={
                "nombre_completo": datos["nombre_completo"],
                "identificacion": datos["identificacion"],
                "email": datos["email"],
                "rol": rol,
            },
        )
        # Siempre se restablece la contraseña para que las credenciales del README funcionen
        usuario.rol = rol
        usuario.is_active = True
        usuario.set_password(datos["password"])  # Se guarda con Argon2id
        usuario.save()

        estado = "Creado" if creado else "Actualizado"
        self.stdout.write(f"  {estado}: {usuario.username} ({rol.nombre})")
        return usuario

    def _crear_salas_y_reservas(self, gestor):
        # AJUSTAR: nombres de modelos y campos según la app del integrante 2
        Sala = apps.get_model("reservas", "Sala")
        Reserva = apps.get_model("reservas", "Reserva")

        manana = timezone.localdate() + timedelta(days=2)  # RN-4.3: >= 24 h de anticipación
        tz = timezone.get_current_timezone()

        for i, datos in enumerate(SALAS_SEMILLA):
            sala, _ = Sala.objects.get_or_create(
                nombre=datos["nombre"],
                defaults={
                    "capacidad": datos["capacidad"],
                    "equipo_disponible": datos["equipo"],
                    "estado": "disponible",
                },
            )

            inicio = datetime.combine(manana + timedelta(days=i), time(9, 0), tzinfo=tz)
            fin = inicio + timedelta(hours=2)  # RN-4.1 y RN-4.2: fin > inicio, máx. 3 h
            Reserva.objects.get_or_create(
                sala=sala,
                fecha_inicio=inicio,
                defaults={
                    "fecha_fin": fin,
                    "solicitante": f"Solicitante de ejemplo {i + 1}",
                    "creado_por": gestor,
                },
            )
            self.stdout.write(f"  Sala y reserva: {sala.nombre}")