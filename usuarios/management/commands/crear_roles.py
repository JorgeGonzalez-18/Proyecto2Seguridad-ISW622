from django.core.management.base import BaseCommand
from usuarios.models import Rol, Usuario


class Command(BaseCommand):
    help = "Crea los 3 roles base con sus permisos granulares y un superusuario inicial"

    def handle(self, *args, **kwargs):
        # definicion de roles y permisos
        roles_data = [
            {
                "nombre": "SuperAdmin",
                "descripcion": "Acceso total: gestión de usuarios, roles, auditoría y reportes.",
                "puede_crear": True,
                "puede_editar": True,
                "puede_borrar": True,
                "puede_ver_reportes": True,
            },
            {
                "nombre": "Auditor",
                "descripcion": "Solo lectura de usuarios y entidad principal, acceso a reportes.",
                "puede_crear": False,
                "puede_editar": False,
                "puede_borrar": False,
                "puede_ver_reportes": True,
            },
            {
                "nombre": "Gestor de reservas",
                "descripcion": "Rol operativo: gestión de salas y reservas. Solo lectura de usuarios.",
                "puede_crear": True,
                "puede_editar": True,
                "puede_borrar": True,
                "puede_ver_reportes": False,
            },
        ]

        # crear o actualizar roles
        for r_info in roles_data:
            rol, created = Rol.objects.get_or_create(
                nombre=r_info["nombre"], defaults=r_info
            )
            if not created:
                rol.descripcion = r_info["descripcion"]
                rol.puede_crear = r_info["puede_crear"]
                rol.puede_editar = r_info["puede_editar"]
                rol.puede_borrar = r_info["puede_borrar"]
                rol.puede_ver_reportes = r_info["puede_ver_reportes"]
                rol.save()
            estado = "Creado" if created else "Actualizado"
            self.stdout.write(self.style.SUCCESS(f"{estado} rol: {rol.nombre}"))
        # creacion de superadmin inicial para las pruebas
        rol_admin = Rol.objects.get(nombre="SuperAdmin")
        username_admin = "admin"

        if not Usuario.objects.filter(username=username_admin).exists():
            admin_user = Usuario.objects.create_superuser(
                username=username_admin,
                email="admin@proyecto2.seguridad",
                password="Admin123456*!",  # Contraseña hasheada automáticamente con Argon2id
                nombre_completo="Administrador Principal",
                identificacion="101110111",
                rol=rol_admin,
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"[Creado] Usuario {admin_user.username} (SuperAdmin) con hash Argon2id"
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(f"El usuario '{username_admin}' ya existe")
            )
