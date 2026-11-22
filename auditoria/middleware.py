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
