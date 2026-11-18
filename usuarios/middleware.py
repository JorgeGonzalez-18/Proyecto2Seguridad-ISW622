import time
from urllib import request, response
from django.conf import settings
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse


class InactividadSesionMiddleware:
    """ """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            ahora = time.time()
            ultima_actividad = request.session.get("Ultima_actividad")

            tiempo_limite = getattr(settings, "TIEMPO_INACTIVIDAD_SEGUNDOS", 60)

            if ultima_actividad is not None:
                tiempo_inactivo = ahora - ultima_actividad

                # cerrar sesion por inactividad
                if tiempo_inactivo > tiempo_limite:
                    logout(request)
                    request.session.flush()
                    messages.warning(
                        request,
                        f"Su sesión ha expirado por inactividad ({tiempo_limite} segundos). Por favor inicie sesión nuevamente.",
                    )

                    # redirige al login
                    try:
                        login_url = reverse("login")
                    except Exception:
                        login_url = "/admin/login/"
                    return redirect(login_url)

            # actualiza tiempo de ultima actividad
            request.session["ultima_actividad"] = ahora

        response = self.get_response(request)
        return response
