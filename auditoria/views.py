from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render
from django.utils import timezone

from usuarios.decorators import requiere_rol

from .models import LogAuditoria


def _parsear_fecha(valor):
    try:
        return datetime.strptime(valor, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


@login_required(login_url="login")
@requiere_rol(["SuperAdmin"])
def panel_auditoria(request):
    """
    UTN-09: Panel de auditoría accesible únicamente por el SuperAdmin.
    Cualquier otro rol recibe HTTP 403 (que a su vez queda auditado).
    Filtros: tipo de evento, usuario, rango de fechas. Paginado.
    """
    logs = LogAuditoria.objects.select_related("usuario").all()

    tipo = request.GET.get("tipo", "")
    usuario = request.GET.get("usuario", "").strip()
    desde = _parsear_fecha(request.GET.get("desde"))
    hasta = _parsear_fecha(request.GET.get("hasta"))

    if tipo in dict(LogAuditoria.TIPOS_EVENTO):
        logs = logs.filter(tipo_evento=tipo)
    else:
        tipo = ""
    if usuario:
        logs = logs.filter(username_intentado__icontains=usuario)
    if desde:
        inicio = timezone.make_aware(datetime.combine(desde, datetime.min.time()))
        logs = logs.filter(fecha__gte=inicio)
    if hasta:
        fin = timezone.make_aware(datetime.combine(hasta + timedelta(days=1), datetime.min.time()))
        logs = logs.filter(fecha__lt=fin)

    paginador = Paginator(logs, 25)
    pagina = paginador.get_page(request.GET.get("page"))

    # Conserva los filtros en los enlaces de paginación
    params = request.GET.copy()
    params.pop("page", None)

    return render(
        request,
        "auditoria/panel.html",
        {
            "pagina": pagina,
            "tipos": LogAuditoria.TIPOS_EVENTO,
            "filtros": {
                "tipo": tipo,
                "usuario": usuario,
                "desde": request.GET.get("desde", "") if desde else "",
                "hasta": request.GET.get("hasta", "") if hasta else "",
            },
            "querystring": params.urlencode(),
            "total": paginador.count,
        },
    )
