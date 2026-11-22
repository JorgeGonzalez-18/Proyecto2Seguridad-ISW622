from django.conf import settings
from django.db import models


class LogAuditoria(models.Model):
    """
    UTN-09: Registro de auditoría de eventos de seguridad.
    Guarda inicios de sesión (exitosos/fallidos), cambios de roles/permisos
    y accesos denegados (HTTP 403).
    """

    TIPO_LOGIN_EXITOSO = "LOGIN_OK"
    TIPO_LOGIN_FALLIDO = "LOGIN_FAIL"
    TIPO_CAMBIO_ROL = "ROL_CAMBIO"
    TIPO_ACCESO_DENEGADO = "ACCESO_403"

    TIPOS_EVENTO = [
        (TIPO_LOGIN_EXITOSO, "Inicio de sesión exitoso"),
        (TIPO_LOGIN_FALLIDO, "Inicio de sesión fallido"),
        (TIPO_CAMBIO_ROL, "Cambio de rol o permisos"),
        (TIPO_ACCESO_DENEGADO, "Acceso denegado (403)"),
    ]

    fecha = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="Fecha y hora")
    tipo_evento = models.CharField(
        max_length=20, choices=TIPOS_EVENTO, db_index=True, verbose_name="Tipo de evento"
    )
    # Usuario que ejecuta la acción (null en logins fallidos con usuario inexistente)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="logs_auditoria",
        verbose_name="Usuario",
    )
    # Nombre de usuario en texto: se conserva aunque el usuario sea eliminado
    username_intentado = models.CharField(max_length=150, blank=True, verbose_name="Username")
    # Usuario afectado (para cambios de roles/permisos: "a quién")
    usuario_afectado = models.CharField(max_length=150, blank=True, verbose_name="Usuario afectado")
    ip = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP")
    ruta = models.CharField(max_length=500, blank=True, verbose_name="Ruta")
    detalle = models.TextField(blank=True, verbose_name="Detalle")

    class Meta:
        verbose_name = "Registro de auditoría"
        verbose_name_plural = "Registros de auditoría"
        ordering = ["-fecha"]

    def __str__(self):
        return f"[{self.fecha:%Y-%m-%d %H:%M:%S}] {self.get_tipo_evento_display()} - {self.username_intentado or 'anónimo'}"

    # Los logs son inmutables: no se pueden editar una vez creados
    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise PermissionError("Los registros de auditoría no pueden modificarse.")
        super().save(*args, **kwargs)
