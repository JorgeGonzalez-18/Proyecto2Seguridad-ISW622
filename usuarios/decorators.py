from functools import wraps
from django.core.exceptions import PermissionDenied


def requiere_permiso(permiso):
    """
    UTN-05: Valida permisos granulares (crear, editar, borrar, ver_reportes).
    Los permisos se evalúan sobre el Rol del usuario autenticado.
    Si no tiene permiso, lanza PermissionDenied que responde HTTP 403.
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                raise PermissionDenied(
                    "Debe iniciar sesión para acceder a este recurso."
                )

            # El SuperAdmin del sistema o superusuarios tienen acceso total
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            rol = getattr(request.user, "rol", None)
            if not rol:
                raise PermissionDenied("El usuario no tiene un rol asignado.")

            # Mapeo de permisos granulares según el modelo Rol
            permisos_map = {
                "crear": rol.puede_crear,
                "editar": rol.puede_editar,
                "borrar": rol.puede_borrar,
                "ver_reportes": rol.puede_ver_reportes,
            }

            if not permisos_map.get(permiso, False):
                raise PermissionDenied(
                    f"Su rol ({rol.nombre}) no cuenta con el permiso '{permiso}'."
                )

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator


def requiere_rol(roles_permitidos):
    """
    UTN-06: Valida que el usuario pertenezca a uno de los roles autorizados.
    Ejemplo: @requiere_rol(['SuperAdmin'])
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                raise PermissionDenied(
                    "Debe iniciar sesión para acceder a este recurso."
                )

            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            rol = getattr(request.user, "rol", None)
            if not rol or rol.nombre not in roles_permitidos:
                raise PermissionDenied("Acceso restringido para su rol actual.")

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator
