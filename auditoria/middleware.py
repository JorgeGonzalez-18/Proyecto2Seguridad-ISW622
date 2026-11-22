from contextvars import ContextVar

_request_actual = ContextVar("auditoria_request_actual", default=None)


def obtener_request_actual():
    """Devuelve la petición HTTP en curso (o None fuera de una petición)."""
    return _request_actual.get()


class RequestActualMiddleware:
    """
    Guarda la petición actual para que las señales de modelo (que no reciben
    `request`) puedan saber quién ejecutó el cambio y desde qué IP.
    Debe ubicarse después de AuthenticationMiddleware.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = _request_actual.set(request)
        try:
            return self.get_response(request)
        finally:
            _request_actual.reset(token)


class Acceso403AuditMiddleware:
    """
    UTN-09: Registra todo acceso denegado (HTTP 403) con la ruta intentada,
    el usuario, la IP y la hora. Cubre PermissionDenied, fallos CSRF y
    cualquier otra respuesta 403 del sistema.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if response.status_code == 403:
            from .models import LogAuditoria
            from .utils import registrar_evento

            usuario = getattr(request, "user", None)
            autenticado = bool(usuario and usuario.is_authenticated)
            registrar_evento(
                LogAuditoria.TIPO_ACCESO_DENEGADO,
                request=request,
                usuario=usuario if autenticado else None,
                username=usuario.get_username() if autenticado else "anónimo",
                detalle=f"Acceso denegado (403) con método {request.method}.",
            )
        return response
