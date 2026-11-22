from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.dispatch import receiver

from .models import LogAuditoria
from .utils import registrar_evento


@receiver(user_logged_in)
def registrar_login_exitoso(sender, request, user, **kwargs):
    """UTN-09: Registra cada inicio de sesión exitoso (fecha, hora e IP real)."""
    registrar_evento(
        LogAuditoria.TIPO_LOGIN_EXITOSO,
        request=request,
        usuario=user,
        username=user.get_username(),
        detalle="Inicio de sesión exitoso.",
    )


@receiver(user_login_failed)
def registrar_login_fallido(sender, credentials, request=None, **kwargs):
    """UTN-09: Registra cada intento de inicio de sesión fallido (fecha, hora e IP real)."""
    # Nunca se guarda la contraseña; solo el username intentado (truncado)
    username = str(credentials.get("username", ""))[:150]
    registrar_evento(
        LogAuditoria.TIPO_LOGIN_FALLIDO,
        request=request,
        username=username,
        detalle="Intento de inicio de sesión fallido: credenciales inválidas.",
    )
