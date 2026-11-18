from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Rol, Usuario

# Register your models here.


@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "descripcion",
        "puede_crear",
        "puede_editar",
        "puede_borrar",
        "puede_ver_reportes",
    )
    search_fields = "nombre"


@admin.register(Usuario)
class UsuarioPersonalizadoAdmin(UserAdmin):
    list_display = (
        "username",
        "email",
        "nombre_completo",
        "rol",
        "last_login",
        "is_active",
    )  # fecha y hora del ultimo inicio de sesión
    list_filter = ("rol", "is_active")

    # Campos que se muestran en el formulario de edición
    fieldsets = UserAdmin.fieldsets = (
        (
            "Información del Proyecto (RBAC y Auditoría)",
            {
                "fields": ("identificacion", "nombre_completo", "rol"),
            },
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets = (
        (
            "Información del Proyecto (RBAC y Auditoría)",
            {
                "fields": ("identificacion", "nombre_completo", "rol"),
            },
        ),
    )
