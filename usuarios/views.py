from django.shortcuts import render

# Create your views here.


def error_403(request, exception=None):
    """
    UTN-06: Manejador seguro de error HTTP 403 Forbidden.
    Retorna la plantilla limpia sin exponer datos ni trazas internas.
    """
    return render(request, "403.html", status=403)
