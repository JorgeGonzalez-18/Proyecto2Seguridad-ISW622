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


# ==========================================================
# UTN-09: Cambios de roles y permisos (quién, a quién, cuándo)
# ==========================================================
from django.db.models.signals import post_delete, post_save, pre_save  # noqa: E402

from usuarios.models import Rol, Usuario  # noqa: E402

from .middleware import obtener_request_actual  # noqa: E402

CAMPOS_PERMISOS = {
    "puede_crear": "Crear",
    "puede_editar": "Editar",
    "puede_borrar": "Borrar",
    "puede_ver_reportes": "Ver reportes",
}


def _actor():
    """Devuelve (request, usuario que ejecuta el cambio)."""
    request = obtener_request_actual()
    actor = getattr(request, "user", None) if request else None
    return request, actor


def _registrar_cambio(afectado, detalle):
    request, actor = _actor()
    registrar_evento(
        LogAuditoria.TIPO_CAMBIO_ROL,
        request=request,
        usuario=actor,
        username=actor.get_username() if actor and actor.is_authenticated else "sistema",
        usuario_afectado=afectado,
        detalle=detalle,
    )


@receiver(pre_save, sender=Rol)
def guardar_estado_previo_rol(sender, instance, **kwargs):
    instance._estado_previo = (
        Rol.objects.filter(pk=instance.pk).first() if instance.pk else None
    )


@receiver(post_save, sender=Rol)
def auditar_rol_guardado(sender, instance, created, **kwargs):
    if created:
        activos = [n for c, n in CAMPOS_PERMISOS.items() if getattr(instance, c)]
        _registrar_cambio(
            f"Rol: {instance.nombre}",
            f"Rol creado con permisos: {', '.join(activos) or 'ninguno'}.",
        )
        return
    previo = getattr(instance, "_estado_previo", None)
    if previo is None:
        return
    cambios = []
    if previo.nombre != instance.nombre:
        cambios.append(f"nombre '{previo.nombre}' -> '{instance.nombre}'")
    for campo, etiqueta in CAMPOS_PERMISOS.items():
        antes, despues = getattr(previo, campo), getattr(instance, campo)
        if antes != despues:
            cambios.append(f"permiso {etiqueta}: {'sí' if antes else 'no'} -> {'sí' if despues else 'no'}")
    if cambios:
        _registrar_cambio(f"Rol: {instance.nombre}", "Rol modificado: " + "; ".join(cambios) + ".")


@receiver(post_delete, sender=Rol)
def auditar_rol_eliminado(sender, instance, **kwargs):
    _registrar_cambio(f"Rol: {instance.nombre}", "Rol eliminado.")


@receiver(pre_save, sender=Usuario)
def guardar_rol_previo_usuario(sender, instance, **kwargs):
    instance._rol_previo_id = (
        Usuario.objects.filter(pk=instance.pk).values_list("rol_id", flat=True).first()
        if instance.pk
        else None
    )


@receiver(post_save, sender=Usuario)
def auditar_rol_de_usuario(sender, instance, created, **kwargs):
    previo_id = getattr(instance, "_rol_previo_id", None)
    if created:
        if instance.rol_id is None:
            return
        detalle = f"Usuario creado con rol '{instance.rol}'."
    elif previo_id != instance.rol_id:
        anterior = Rol.objects.filter(pk=previo_id).first()
        detalle = (
            f"Rol del usuario cambiado: '{anterior.nombre if anterior else 'Sin rol'}' "
            f"-> '{instance.rol.nombre if instance.rol else 'Sin rol'}'."
        )
    else:
        return
    _registrar_cambio(instance.username, detalle)
