from django.urls import path
from . import views

app_name = "reservas"

urlpatterns = [
    # Catálogo de Salas (RFD-4.1)
    path("salas/", views.lista_salas_view, name="lista_salas"),
    path("salas/nueva/", views.crear_sala_view, name="crear_sala"),
    path("salas/<int:pk>/editar/", views.editar_sala_view, name="editar_sala"),

    # Gestión de Reservas (RFD-4.2 y RFD-4.4)
    path("", views.lista_reservas_view, name="lista_reservas"),
    path("nueva/", views.crear_reserva_view, name="crear_reserva"),
    path("<str:codigo>/", views.detalle_reserva_view, name="detalle_reserva"),
    path("<str:codigo>/cancelar/", views.cancelar_reserva_view, name="cancelar_reserva"),
]