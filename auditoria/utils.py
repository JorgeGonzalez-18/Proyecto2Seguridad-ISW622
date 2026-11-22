from .models import LogAuditoria


def obtener_ip_cliente(request):
    """
    Obtiene la IP real del cliente.
    Detrás de un proxy (Render/Railway) la IP real viene en X-Forwarded-For
    (el primer valor de la lista); si no existe, se usa REMOTE_ADDR.
    """
    if request is None:
        return None
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip() or None
    return request.META.get("REMOTE_ADDR") or None


def registrar_evento(tipo_evento, request=None, usuario=None, username="",
                     usuario_afectado="", detalle="", ruta=None):
    """Crea un registro de auditoría. Nunca debe romper el flujo de la petición."""
    try:
        if usuario is not None and not getattr(usuario, "is_authenticated", False):
            usuario = None
        if ruta is None and request is not None:
            ruta = request.get_full_path()
        return LogAuditoria.objects.create(
            tipo_evento=tipo_evento,
            usuario=usuario,
            username_intentado=username or (usuario.get_username() if usuario else ""),
            usuario_afectado=usuario_afectado,
            ip=obtener_ip_cliente(request),
            ruta=(ruta or "")[:500],
            detalle=detalle,
        )
    except Exception:
        return None
