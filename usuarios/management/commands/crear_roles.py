from django.core.management.base import BaseCommand
from usuarios.models import Rol, Usuario


class Command(BaseCommand):
    help = (
        "Crea los 3 roles base (UTN-06) y los 3 usuarios de prueba del README (UTN-04)"
    )

    def handle(self, *args, **kwargs):
        # 1. Definición de roles y permisos granulares (UTN-05 y UTN-06)
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

        roles_map = {}
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
            roles_map[rol.nombre] = rol
            estado = "Creado" if created else "Actualizado"
            self.stdout.write(self.style.SUCCESS(f"[{estado}] Rol: {rol.nombre}"))

        # 2. Creación de los 3 usuarios de prueba documentados en el README.md
        usuarios_prueba = [
            {
                "username": "admin",
                "email": "admin@proyecto2.seguridad",
                "password": "Admin123456*!",
                "nombre_completo": "Administrador Principal",
                "identificacion": "101110111",
                "rol": roles_map["SuperAdmin"],
                "superuser": True,
            },
            {
                "username": "auditor",
                "email": "auditor@proyecto2.seguridad",
                "password": "Auditor123*!",
                "nombre_completo": "Auditor de Seguridad",
                "identificacion": "202220222",
                "rol": roles_map["Auditor"],
                "superuser": False,
            },
            {
                "username": "gestor",
                "email": "gestor@proyecto2.seguridad",
                "password": "Gestor123*!",
                "nombre_completo": "Gestor de Reservas Campus",
                "identificacion": "303330333",
                "rol": roles_map["Gestor de reservas"],
                "superuser": False,
            },
        ]

        for u_data in usuarios_prueba:
            if not Usuario.objects.filter(username=u_data["username"]).exists():
                if u_data["superuser"]:
                    user = Usuario.objects.create_superuser(
                        username=u_data["username"],
                        email=u_data["email"],
                        password=u_data["password"],
                        nombre_completo=u_data["nombre_completo"],
                        identificacion=u_data["identificacion"],
                        rol=u_data["rol"],
                    )
                else:
                    user = Usuario.objects.create_user(
                        username=u_data["username"],
                        email=u_data["email"],
                        password=u_data["password"],
                        nombre_completo=u_data["nombre_completo"],
                        identificacion=u_data["identificacion"],
                        rol=u_data["rol"],
                    )
                self.stdout.write(
                    self.style.SUCCESS(
                        f"[Creado] Usuario '{user.username}' ({user.rol.nombre}) con hash Argon2id"
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f"El usuario '{u_data['username']}' ya existe.")
                )
