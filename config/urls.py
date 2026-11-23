from django.contrib import admin
from django.urls import path, include
from usuarios.views import inicio_view

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", inicio_view, name="inicio"),
    path("", include("usuarios.urls")),
    path("", include("auditoria.urls")),
]

# UTN-06: Manejador global del error HTTP 403 Forbidden
handler403 = "usuarios.views.error_403"
