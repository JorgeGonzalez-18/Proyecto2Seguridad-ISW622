from django.contrib import admin

from .models import LogAuditoria


@admin.register(LogAuditoria)
class LogAuditoriaAdmin(admin.ModelAdmin):
    list_display = ("fecha", "tipo_evento", "username_intentado", "ip", "ruta")
    list_filter = ("tipo_evento", "fecha")
    search_fields = ("username_intentado", "usuario_afectado", "ip", "ruta")

    # Solo lectura: la auditoría no se altera desde el admin
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
